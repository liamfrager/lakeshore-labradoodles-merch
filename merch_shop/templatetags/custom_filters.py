from django import template

register = template.Library()


@register.filter
def cents_to_dollars(value):
    try:
        return "{:.2f}".format(value / 100)
    except (ValueError, TypeError):
        return value


@register.filter
def total_price(value):
    try:
        return cents_to_dollars(value['price']['unit_amount'] * value['quantity'])
    except (ValueError, TypeError):
        return value


@register.filter
def first_word(value: str):
    try:
        return value.split(' ')[0]
    except (ValueError, TypeError):
        return value
