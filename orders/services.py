from collections import defaultdict
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from catalog.models import Product
from .models import Order, OrderItem

TRANSITIONS = {
    'Pending': ['Confirmed', 'Cancelled'],
    'Confirmed': ['Shipped', 'Cancelled'],
    'Shipped': ['Completed'],
    'Completed': [],
    'Cancelled': [],
}


@transaction.atomic
def place_order(user, cart, shipping):
    if not cart:
        raise ValueError('Your bag is empty.')
    wanted = defaultdict(int)
    products = Product.objects.select_for_update().filter(pk__in=[x['product_id'] for x in cart.values()]).in_bulk()
    total = Decimal('0.00')
    for item in cart.values():
        product = products.get(item['product_id'])
        if not product or not product.is_active:
            raise ValueError('An item is no longer available. Please update your bag.')
        quantity = item['quantity']
        if not isinstance(quantity, int) or quantity < 1 or quantity > 99 or item['size'] not in (product.sizes or ['One size']):
            raise ValueError('An item has an invalid quantity or size. Please update your bag.')
        wanted[product.pk] += quantity
        total += product.price * quantity
    for pk, quantity in sorted(wanted.items()):
        # Conditional decrement also protects stock on SQLite, which has no row locks.
        if Product.objects.filter(pk=pk, is_active=True, stock__gte=quantity).update(stock=F('stock') - quantity, updated_at=timezone.now()) != 1:
            raise ValueError(f'Not enough stock for {products[pk].short_name}. Please update your bag.')
    order = Order.objects.create(user=user, total=total, **shipping)
    OrderItem.objects.bulk_create([OrderItem(order=order, product=products[x['product_id']], name=products[x['product_id']].name, price=products[x['product_id']].price, quantity=x['quantity'], size=x['size'], color=products[x['product_id']].color) for x in cart.values()])
    return order


@transaction.atomic
def transition_order(order_id, status):
    order = Order.objects.select_for_update().get(pk=order_id)
    if status not in TRANSITIONS[order.status]:
        raise ValueError(f'Cannot change {order.status} to {status}.')
    # Compare-and-swap makes cancellation and stock restoration happen once.
    changed = Order.objects.filter(pk=order.pk, status=order.status).update(status=status, updated_at=timezone.now())
    if not changed:
        raise ValueError('Order changed. Refresh and try again.')
    if status == Order.Status.CANCELLED:
        for item in order.items.all():
            if item.product_id:
                Product.objects.filter(pk=item.product_id).update(stock=F('stock') + item.quantity, updated_at=timezone.now())
    return order
