from django.urls import path
from . import views
urlpatterns = [
    path('cart/', views.cart, name='cart'), path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'), path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:reference>/', views.order_detail, name='order_detail'),
    path('orders/<uuid:reference>/success/', views.order_detail, {'success': True}, name='order_success'),
]

