from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, ProtectedError, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order
from orders.services import TRANSITIONS, transition_order
from .forms import CategoryForm, ProductForm, UserForm
from .permissions import admin_required


@admin_required
def index(request):
    return render(request, 'dashboard/index.html', {
        'product_count': Product.objects.count(), 'user_count': User.objects.count(), 'order_count': Order.objects.count(),
        'pending_count': Order.objects.filter(status='Pending').count(), 'low_count': Product.objects.filter(stock__lte=5, is_active=True).count(),
        'low_stock': Product.objects.filter(stock__lte=5, is_active=True)[:6],
        'recent_orders': Order.objects.select_related('user')[:6],
        'revenue': Order.objects.exclude(status='Cancelled').aggregate(total=Sum('total'))['total'] or 0,
    })


CONFIG = {
    'products': (Product, ProductForm, 'Products'),
    'categories': (Category, CategoryForm, 'Categories'),
    'users': (User, UserForm, 'Users'),
}


@admin_required
def entity_list(request, kind):
    model, _, title = CONFIG[kind]
    objects = model.objects.all()
    query = request.GET.get('q', '').strip()
    if kind == 'products':
        objects = objects.select_related('category')
        if query:
            objects = objects.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
    elif kind == 'users':
        objects = objects.order_by('-date_joined')
        if query:
            objects = objects.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    else:
        objects = objects.annotate(product_count=Count('products')).order_by('id')
        if query:
            objects = objects.filter(name__icontains=query)
    return render(request, 'dashboard/list.html', {'kind': kind, 'title': title, 'page_obj': Paginator(objects, 12).get_page(request.GET.get('page')), 'query': query})


def guard_user(actor, target, *, deleting=False, cleaned=None):
    if target.is_superuser and not actor.is_superuser:
        raise PermissionDenied('Only a superuser can manage another superuser.')
    cleaned = cleaned or {}
    losing_access = deleting or cleaned.get('is_active') is False or cleaned.get('role', target.role) != User.Role.ADMIN
    if actor.pk == target.pk and losing_access:
        raise ValueError('You cannot delete, disable, or remove your own admin role.')
    if target.is_superuser and losing_access:
        raise ValueError('Superusers are protected. Manage superuser access using Django management commands.')
    if target.is_store_admin and losing_access:
        if not User.objects.filter(is_active=True).filter(Q(role='admin') | Q(is_superuser=True)).exclude(pk=target.pk).exists():
            raise ValueError('Keep at least one active admin account.')


@admin_required
def entity_edit(request, kind, pk=None):
    model, form_class, title = CONFIG[kind]
    instance = get_object_or_404(model, pk=pk) if pk else model()
    if kind == 'users' and instance.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if kind == 'users' and pk:
                    list(User.objects.select_for_update().filter(Q(role='admin') | Q(is_superuser=True)).values_list('pk', flat=True))
                    original = User.objects.get(pk=pk)
                    guard_user(request.user, original, cleaned=form.cleaned_data)
                form.save()
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            singular_title = {'products': 'Product', 'categories': 'Category', 'users': 'User'}[kind]
            messages.success(request, f'{singular_title} saved successfully.')
            return redirect(f'dashboard_{kind}')
    singular = {'products': 'product', 'categories': 'category', 'users': 'user'}[kind]
    return render(request, 'dashboard/form.html', {'form': form, 'title': f'{"Edit" if pk else "Add"} {singular}', 'kind': kind, 'object': instance})


@admin_required
def entity_delete(request, kind, pk):
    model, _, title = CONFIG[kind]
    obj = get_object_or_404(model, pk=pk)
    if kind == 'users' and obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if kind == 'users':
                    list(User.objects.select_for_update().filter(Q(role='admin') | Q(is_superuser=True)).values_list('pk', flat=True))
                    guard_user(request.user, obj, deleting=True)
                obj.delete()
        except (ValueError, ProtectedError) as exc:
            messages.error(request, 'Move or delete the products in this category first.' if isinstance(exc, ProtectedError) else str(exc))
        else:
            messages.success(request, 'Deleted successfully.')
        return redirect(f'dashboard_{kind}')
    return render(request, 'dashboard/delete.html', {'object': obj, 'kind': kind, 'title': 'Confirm deletion'})


@admin_required
@require_POST
def user_toggle(request, pk):
    with transaction.atomic():
        list(User.objects.select_for_update().filter(Q(role='admin') | Q(is_superuser=True)).values_list('pk', flat=True))
        user = get_object_or_404(User.objects.select_for_update(), pk=pk)
        try:
            guard_user(request.user, user, cleaned={'is_active': not user.is_active})
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            messages.success(request, 'User status updated.')
    return redirect('dashboard_users')


@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'dashboard/user_detail.html', {'member': user, 'title': user.username, 'kind': 'users'})


@admin_required
def product_preview(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('additional_images'), pk=pk)
    return render(request, 'dashboard/product_preview.html', {'product': product, 'title': product.name, 'kind': 'products'})


@admin_required
def order_list(request):
    orders = Order.objects.select_related('user')
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'dashboard/orders.html', {'page_obj': Paginator(orders, 15).get_page(request.GET.get('page')), 'statuses': Order.Status.choices, 'title': 'Orders', 'kind': 'orders'})


@admin_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    if request.method == 'POST':
        try:
            transition_order(order.pk, request.POST.get('status'))
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, 'Order status updated.')
        return redirect('dashboard_order_detail', pk=pk)
    return render(request, 'dashboard/order_detail.html', {'order': order, 'transitions': TRANSITIONS[order.status], 'title': order.number, 'kind': 'orders'})
