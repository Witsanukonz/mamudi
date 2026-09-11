import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import cart_lines, change_cart
from .forms import CheckoutForm
from .models import Order
from .services import place_order


def cart(request):
    lines, total = cart_lines(request)
    return render(request, 'orders/cart.html', {'lines': lines, 'total': total})


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        quantity = int(request.POST.get('quantity', '1'))
        if quantity < 1:
            raise ValueError('Choose at least one item.')
        change_cart(request, product, request.POST.get('size', ''), quantity)
        messages.success(request, f'{product.short_name} added to your bag.')
    except (ValueError, TypeError) as exc:
        messages.error(request, str(exc))
    return redirect('cart')


@require_POST
def cart_update(request):
    key = request.POST.get('key', '')
    items = request.session.get('cart', {}).copy()
    item = items.get(key)
    if item:
        if request.POST.get('action') == 'remove':
            items.pop(key)
            request.session['cart'] = items
        else:
            product = Product.objects.filter(pk=item['product_id']).first()
            if not product:
                items.pop(key)
                request.session['cart'] = items
            else:
                try:
                    quantity = int(request.POST.get('quantity', item['quantity']))
                    if request.POST.get('action') == 'plus':
                        quantity = item['quantity'] + 1
                    elif request.POST.get('action') == 'minus':
                        quantity = item['quantity'] - 1
                    change_cart(request, product, item['size'], quantity, replace=True)
                except (ValueError, TypeError) as exc:
                    messages.error(request, str(exc))
    return redirect('cart')


@login_required
def checkout(request):
    token = request.POST.get('checkout_token')
    if request.method == 'POST' and token:
        try:
            prior = Order.objects.filter(reference=uuid.UUID(token), user=request.user).first()
        except ValueError:
            prior = None
        if prior:
            return redirect('order_success', reference=prior.reference)
    lines, total = cart_lines(request)
    if not lines:
        messages.info(request, 'Add something to your bag first.')
        return redirect('cart')
    if 'checkout_token' not in request.session:
        request.session['checkout_token'] = str(uuid.uuid4())
    initial = {key: getattr(request.user, key) for key in ['phone', 'address', 'province', 'postal_code']}
    initial.update(full_name=request.user.get_full_name(), checkout_token=request.session['checkout_token'])
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data.copy()
        reference = data.pop('checkout_token')
        if str(reference) != request.session.get('checkout_token'):
            form.add_error(None, 'This checkout expired. Reload the page and try again.')
        else:
            try:
                order = place_order(request.user, request.session.get('cart', {}), {**data, 'reference': reference})
            except ValueError as exc:
                form.add_error(None, str(exc))
            except IntegrityError:
                order = Order.objects.filter(reference=reference, user=request.user).first()
                if order is None:
                    raise
            else:
                request.session['cart'] = {}
                request.session.pop('checkout_token', None)
                return redirect('order_success', reference=order.reference)
            if not form.errors and order:
                return redirect('order_success', reference=order.reference)
    return render(request, 'orders/checkout.html', {'form': form, 'lines': lines, 'total': total})


@login_required
def order_list(request):
    return render(request, 'orders/list.html', {'orders': request.user.orders.prefetch_related('items')})


@login_required
def order_detail(request, reference, success=False):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), reference=reference, user=request.user)
    return render(request, 'orders/detail.html', {'order': order, 'success': success})

