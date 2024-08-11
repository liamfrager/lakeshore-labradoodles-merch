import os
import requests
import stripe
from .models import Product, Color

PRINTFUL_AUTH_TOKEN = os.getenv('PRINTFUL_AUTH_TOKEN')
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')


class Printful():
    '''A class that interacts with the Printful API. Initialize with store specific auth token from Printful to link this object with your store.'''

    def __init__(self, auth_token: str) -> None:
        self.auth_token = auth_token
        self.api_endpoint = 'https://api.printful.com/'
        self.api_headers = {
            'Authorization': 'Bearer ' + self.auth_token
        }

    def get_all_products(self) -> list[dict]:
        '''Returns all sync products from the Printful shop.'''
        response = requests.get(
            url=self.api_endpoint + 'sync/products',
            headers=self.api_headers,
            params={'status': 'all'},
        )
        return response.json()['result']

    def get_product(self, id: int) -> dict:
        '''Takes a Printful sync product ID as an input and returns details on the product.'''
        response = requests.get(
            url=self.api_endpoint + 'sync/products/' + str(id),
            headers=self.api_headers,
            params={'limit': 100},
        )
        return response.json()['result']

    def get_variant_ids(self, id: int) -> dict:
        '''Takes a Printful sync product ID as an input and returns details on all its variants.'''
        product = self.get_product(id)
        variants_ids = [variant['id'] for variant in product['sync_variants']]
        return variants_ids

    def get_variant(self, id: int) -> dict:
        '''Takes a Printful sync variant ID as an input and returns details on that variant.'''
        response = requests.get(
            url=self.api_endpoint + 'sync/variant/' + str(id),
            headers=self.api_headers,
        )
        return response.json()['result']['sync_variant']

    def get_color_code(self, id: int) -> str:
        '''Takes a Printful product variant ID as an input and returns the color code associated with that variant.'''
        response = requests.get(
            url=self.api_endpoint + 'products/variant/' + str(id),
            headers=self.api_headers,
        )
        return response.json()['result']['variant']['color_code']

    def place_order(self, order):
        response = requests.post(
            url=self.api_endpoint + 'orders',
            headers=self.api_headers,
            json=order,
            # Draft order without processing for fulfilliment. Used for testing.
            params={'confirm': 'false'},
        )
        if response.json()['code'] == 200:
            user_email = order['recipient']['email']
            print(user_email)
        return response.json()


class Stripe():
    '''A class that interacts with the Stripe API. Initialize with Stripe API key to link this object with your account.'''

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        stripe.api_key = self.api_key

    def get_price_data(self, variant):
        '''Takes a Printful variant as an input and returns a dictionary formatted as 'price-data' for the Stripe API session creation.'''
        price_data = {
            'currency': variant['currency'].lower(),
            'unit_amount': variant['retail_price'].replace('.', ''),
            'product_data': {
                'name': variant['name'],
                'description': ' ',  # TODO: Implement product descriptions
                'images': [file['thumbnail_url'] for file in variant['files']],
            },
        }
        return price_data


class Shop():
    def __init__(self) -> None:
        self.printful = Printful(PRINTFUL_AUTH_TOKEN)
        self.stripe = Stripe(STRIPE_API_KEY)

    def get_all_products(self) -> list[Product]:
        '''Returns all product entries in the database or creates them if they don't exist.'''
        # try:
        syncs = self.printful.get_all_products()
        products = []
        for sync in syncs:
            product = Product(
                id=sync['id'],
                name=sync['name'],
                image=sync['thumbnail_url'],
            )
            products.append(product)
        return products

    def get_product(self, id: int) -> Product:
        '''Takes Printful sync product ID as returns a Product object with product details.'''
        sync = self.printful.get_product(id)

        # Create product object
        product = Product(
            id=id,
            name=sync['sync_product']['name'],
            image=sync['sync_product']['thumbnail_url'],
            sizes=[size for size in ['S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'] if size in set([
                variant['size'] for variant in sync['sync_variants']])],
        )

        preview_images = {}
        size_prices = {}
        colors = []
        for variant in sync['sync_variants']:
            # Get product variant images
            color = variant['color']
            if color not in preview_images:
                images = []
                for file in variant['files']:
                    images.append(file['preview_url'])
                preview_images[color] = images
            # Get product variant prices
            size = variant['size']
            if size not in size_prices:
                price = variant['retail_price']
                size_prices[size] = price
            # Get product colors
            try:
                color = Color.objects.get(name=variant['color'])
            except Color.DoesNotExist:
                color = Color.objects.create(
                    name=variant['color'],
                    code=self.printful.get_color_code(
                        variant['product']['variant_id']),
                )
            colors.append(color)

        # Add preview_images, prices, and colors to product
        product.preview_images = preview_images  # add preview images to product object
        product.size_prices = size_prices  # add preview images to product object
        product.colors = set(colors)  # add unique colors to product object
        return product

    def get_variant(self, id, color, size) -> dict:
        '''Takes a Printful sync product ID, color name, and size as an input, and returns details for the corresponding variant.'''
        product = self.printful.get_product(id)
        variant = next(
            variant for variant in product['sync_variants'] if variant['color'] == color and variant['size'] == size)
        return variant

    def get_line_items(self, cart: dict) -> list:
        line_items = []
        for id, item in cart['items'].items():
            variant = self.printful.get_variant(id)
            line_item = {
                'price_data': self.stripe.get_price_data(variant),
                'quantity': item['quantity'],
            }
            line_items.append(line_item)
        return line_items

    def place_order(self, payment_intent: stripe.PaymentIntent):
        '''Takes a Stripe PaymentIntent object as an input and places an order on Printful.'''
        checkout_session = stripe.checkout.Session.list(
            payment_intent=payment_intent.id,
            expand=['data.line_items'],
        ).data[0]
        order = {
            'recipient': {
                'name': checkout_session.shipping_details.name,
                'address1': checkout_session.shipping_details.address.line1,
                'address2': checkout_session.shipping_details.address.line2,
                'city': checkout_session.shipping_details.address.city,
                'state_code': checkout_session.shipping_details.address.state,
                'country_code': checkout_session.shipping_details.address.country,
                'zip': checkout_session.shipping_details.address.postal_code,
                'phone': checkout_session.customer_details.phone,
                'email': checkout_session.customer_details.email,
            },
            'items': [
                {
                    'sync_variant_id': id,
                    'quantity': quantity,
                }
                for id, quantity in checkout_session.metadata.items()
            ],
            'packing_slip': {
                'email': 'lakeshorelabradoodles@gmail.com',
                'phone': '+1(860)478-0267',
                'message': 'Thank you for your purchase!',
                'logo_url': '​http://www.your-domain.com/packing-logo.png',
                'store_name': 'Lakeshore Labradoodles',
            },
        }
        self.printful.place_order(order)
