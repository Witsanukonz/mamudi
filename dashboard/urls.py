from django.urls import path
from . import views

urlpatterns = [path('', views.index, name='dashboard')]
for kind in ['products', 'categories', 'users']:
    urlpatterns += [
        path(f'{kind}/', views.entity_list, {'kind': kind}, name=f'dashboard_{kind}'),
        path(f'{kind}/add/', views.entity_edit, {'kind': kind}, name=f'dashboard_{kind}_add'),
        path(f'{kind}/<int:pk>/edit/', views.entity_edit, {'kind': kind}, name=f'dashboard_{kind}_edit'),
        path(f'{kind}/<int:pk>/delete/', views.entity_delete, {'kind': kind}, name=f'dashboard_{kind}_delete'),
    ]
urlpatterns += [
    path('users/<int:pk>/', views.user_detail, name='dashboard_user_detail'),
    path('users/<int:pk>/toggle/', views.user_toggle, name='dashboard_user_toggle'),
    path('products/<int:pk>/', views.product_preview, name='dashboard_product_preview'),
    path('orders/', views.order_list, name='dashboard_orders'),
    path('orders/<int:pk>/', views.order_detail, name='dashboard_order_detail'),
]
