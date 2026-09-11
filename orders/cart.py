from decimal import Decimal
from catalog.models import Product


def cart_lines(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(pk__in=[x['product_id'] for x in cart.values()]).in_bulk()
    valid_cart = {key: item for key, item in cart.items() if item['product_id'] in products}
    if len(valid_cart) != len(cart):
        request.session['cart'] = valid_cart
        cart = valid_cart
    lines = []
    for key, item in cart.items():
        product = products.get(item['product_id'])
        if product:
            lines.append({'key': key, 'product': product, 'size': item['size'], 'quantity': item['quantity'], 'subtotal': product.price * item['quantity']})
    return lines, sum((line['subtotal'] for line in lines), Decimal('0.00'))


def change_cart(request, product, size, quantity, replace=False):
    allowed = product.sizes or ['One size']
    if size not in allowed:
        raise ValueError('Please choose an available size.')
    if not product.is_active:
        raise ValueError('This product is no longer available.')
    if quantity < 0 or quantity > 99:
        raise ValueError('Quantity must be between 0 and 99.')
    cart = request.session.get('cart', {}).copy()
    key = f'{product.pk}:{size}'
    final = quantity if replace else cart.get(key, {}).get('quantity', 0) + quantity
    others = sum(x['quantity'] for k, x in cart.items() if x['product_id'] == product.pk and k != key)
    if final + others > product.stock or final > 99:
        raise ValueError(f'Only {product.stock} items of {product.short_name} are available across all sizes.')
    if final:
        cart[key] = {'product_id': product.pk, 'size': size, 'quantity': final}
    else:
        cart.pop(key, None)
    request.session['cart'] = cart
