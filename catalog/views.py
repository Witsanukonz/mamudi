from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render
from .models import Category, Product, SIZE_CHOICES


def home(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    best = products.annotate(sold=Sum('order_items__quantity', filter=~Q(order_items__order__status='Cancelled'))).order_by('-sold', '-stock', 'id')[:4]
    return render(request, 'catalog/home.html', {'new_arrivals': products[:4], 'best_sellers': best, 'categories': Category.objects.prefetch_related('products').all()})


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(color__icontains=query))
    for field in ['gender', 'category__slug']:
        value = request.GET.get(field.split('__')[0])
        if value:
            products = products.filter(**{field: value})
    for param, lookup in [('min_price', 'price__gte'), ('max_price', 'price__lte')]:
        try:
            amount = Decimal(request.GET.get(param, ''))
            if amount.is_finite() and amount >= 0:
                products = products.filter(**{lookup: amount})
        except (InvalidOperation, ValueError):
            pass
    size = request.GET.get('size')
    if size in dict(SIZE_CHOICES):
        # Portable on SQLite and PostgreSQL without JSON containment extensions.
        products = products.filter(pk__in=[p.pk for p in products.select_related(None).only('id', 'sizes') if size in p.sizes])
    availability = request.GET.get('availability')
    if availability == 'in_stock':
        products = products.filter(stock__gt=0)
    elif availability == 'out_of_stock':
        products = products.filter(stock=0)
    sort = request.GET.get('sort', 'newest')
    products = products.order_by({'newest': '-release_date', 'price_asc': 'price', 'price_desc': '-price', 'name': 'name'}.get(sort, '-release_date'), '-id')
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'catalog/shop.html', {'page_obj': Paginator(products, 12).get_page(request.GET.get('page')), 'sizes': SIZE_CHOICES, 'filter_query': params.urlencode(), 'query': query})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    related = Product.objects.filter(is_active=True, category=product.category).exclude(pk=product.pk)[:4]
    return render(request, 'catalog/detail.html', {'product': product, 'related': related})
