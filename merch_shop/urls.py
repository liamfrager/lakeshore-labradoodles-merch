from django.urls import path
from . import views

urlpatterns = [
    # ROUTES
    path('', views.home, name='home'),
    path('product/<int:product_id>', views.product, name='product'),
    path('cart', views.cart, name='cart'),
    path('add_to_cart', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:variant_id>',
         views.remove_from_cart, name='remove_from_cart'),
    path('update_quantity', views.update_quantity, name='update_quantity'),
    path('checkout', views.checkout, name='checkout'),
    path('order_success', views.order_success, name='order_success'),
    # WEBHOOKS
    path('stripe_webhooks', views.stripe_webhooks, name='stripe_webhooks')
]
