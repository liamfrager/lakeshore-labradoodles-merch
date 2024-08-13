import stripe
import json
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from .shop import Shop
load_dotenv()

shop = Shop()


# VIEWS
def home(request: HttpRequest):
    products = shop.get_all_products()
    return render(request, 'index.html', {'products': products})


def product(request: HttpRequest, product_id):
    product = shop.get_product(int(product_id))
    return render(request, 'product.html', {'product': product})


def cart(request: HttpRequest):
    cart = request.session.get('cart')
    return render(request, 'cart.html', {'cart': cart})


def add_to_cart(request: HttpRequest):
    if request.method == 'POST':
        cart = request.session.get('cart')
        if cart == None:
            cart = {
                'items': {},
                'order_total': 0,
            }
        variant = shop.get_variant(
            request.POST['product_id'],
            request.POST['color'],
            request.POST['size'],
        )
        cart['items'][variant['id']] = {
            'name': variant['name'],
            'price': float(variant['retail_price']),
            'total_price': float(variant['retail_price']),
            'img': variant['files'][0]['thumbnail_url'],
            'quantity': 1,
        }
        cart['order_total'] = sum(
            [cart['items'][id]['total_price'] for id in cart['items']])
        request.session['cart'] = cart
        request.session.modified = True
        return redirect('cart')
    return 'Could not add to cart.'  # TODO: add better error handling


def remove_from_cart(request: HttpRequest, variant_id):
    cart = request.session.get('cart')
    if cart == None:
        cart = {}
    cart['items'].pop(str(variant_id))
    cart['order_total'] = sum(
        [cart['items'][id]['total_price'] for id in cart['items']])
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')


def update_quantity(request: HttpRequest):
    if request.method == 'POST':
        variant_id = request.POST['variant_id']
        quantity = request.POST['quantity']
        cart = request.session.get('cart')
        cart['items'][variant_id]['quantity'] = int(quantity)
        cart['items'][variant_id]['total_price'] = cart['items'][variant_id]['price'] * \
            int(quantity)
        cart['order_total'] = sum(
            [cart['items'][id]['total_price'] for id in cart['items']])
        request.session['cart'] = cart
        request.session.modified = True
        return redirect('cart')
    return 'Could not add to cart.'  # TODO: add better error handling


def checkout(request: HttpRequest):
    try:
        cart = request.session.get('cart')
        # TODO: verify that all items in the cart still exist/are in stock through printful.
        YOUR_DOMAIN = 'shop.lakeshorelabradoodles.com'
        checkout_session = stripe.checkout.Session.create(
            line_items=shop.get_line_items(cart),
            mode='payment',
            shipping_address_collection={'allowed_countries': ['US']},
            success_url=YOUR_DOMAIN + '/order_success',
            cancel_url=YOUR_DOMAIN + '/cart',
            metadata={id: item['quantity']
                      for id, item in cart['items'].items()}
        )
        request.session['order_success'] = True
        return redirect(checkout_session.url)
    except Exception as e:
        del request.session['order_success']
        return f'Could not checkout. An error occurred: {str(e)}'


def order_success(request: HttpRequest):
    if not request.session.get('order_success'):
        return redirect('home')
    else:
        del request.session['order_success']
        del request.session['cart']
        return render(request, 'success.html')


# WEBHOOKS
@csrf_exempt
def stripe_webhooks(request: HttpRequest):
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        shop.place_order(payment_intent)
    else:
        print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)
