from django.http import HttpRequest


def cart_item_count(request: HttpRequest):
    # Retrieve cart data from the session
    cart = request.session.get('cart', {'items': {}})
    # Calculate the number of items in the cart
    cart_item_count = len([item for item in cart['items']])
    return {
        'cart_item_count': cart_item_count
    }
