from .models import Category


def store_context(request):
    cart = request.session.get('cart', {})
    count = sum(item.get('quantity', 0) for item in cart.values())
    return {'nav_categories': Category.objects.all(), 'cart_count': count}

