from email.message import EmailMessage
from django.conf import settings
import stripe
import json
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
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
        YOUR_DOMAIN = 'https://shop.lakeshorelabradoodles.com'
        checkout_session = stripe.checkout.Session.create(
            line_items=shop.get_line_items(cart),
            mode='payment',
            shipping_address_collection={'allowed_countries': ['US']},
            success_url=YOUR_DOMAIN + '/order_success',
            cancel_url=YOUR_DOMAIN + '/cart',
            metadata={id: item['quantity']
                      for id, item in cart['items'].items()}
        )
        request.session['checkout_success'] = True
        return redirect(checkout_session.url)
    except Exception as e:
        return HttpResponse(f'Could not checkout. An error occurred: {str(e)}')


def order_success(request: HttpRequest):
    if not request.session.get('order_success'):
        return redirect('home')
    else:
        del request.session['checkout_success']
        del request.session['cart']
        return render(request, 'success.html')


def email(request):
    print('ORDER SUCCESSFUL!!!')
    html = render_to_string(
        'emails/order_confirmation.html', {
            'shipping_details': {
                'name': 'Liam Frager',
                'address': {
                    'line1': '6 Percy Dr.',
                    'line2': '',
                    'city': 'Wolfeboro',
                    'state': 'NH',
                    'postal_code': '03894',
                    'country': 'USA',
                },
            },
            'amount_total': 9500,
            'line_items': {
                'data': [
                    {
                        'description': 'Sweatshirt',
                        'quantity': 1,
                        'price': {
                            'unit_amount': 3500
                        }
                    },
                    {
                        'description': 'T-Shirt',
                        'quantity': 3,
                        'price': {
                            'unit_amount': 2000
                        }
                    }
                ]
            }
        })

    email = EmailMultiAlternatives(
        subject='Order Confirmation',
        body='plain text',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=['liam.frager@gmail.com']
    )

    email.attach_alternative(html, 'text/html')

    email.send()


# WEBHOOKS
@csrf_exempt
def stripe_webhooks(request: HttpRequest):
    print('Webhook recieved')
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Payment succeeded
    if event.type == 'payment_intent.succeeded':
        payment_intent: stripe.PaymentIntent = event.data.object
        checkout_session = stripe.checkout.Session.list(
            payment_intent=payment_intent.id,
            expand=['data.line_items'],
        ).data[0]

        order_response = shop.place_order(checkout_session)

        # Order succeeded
        if order_response['code'] == 200:
            html_message = render_to_string(
                'emails/order_confirmation.html',
                checkout_session
            )
            email = EmailMultiAlternatives(
                subject='Order Confirmation',
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[checkout_session.customer_email]
            )
            email.attach_alternative(html_message, 'text/html')
            email.send()
        # Order failed
        else:
            html_message = render_to_string(
                'emails/order_failed.html', {
                    'order_response': order_response,
                    'checkout_session': checkout_session,
                    'payment_intent': payment_intent,
                })
            email = EmailMultiAlternatives(
                subject='Issue with order!',
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['liam.frager@gmail.com']
            )
            email.attach_alternative(html_message, 'text/html')
            email.send()
    # Payment Failed
    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object

    else:
        print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)
