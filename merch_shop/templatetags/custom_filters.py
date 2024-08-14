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
        return "{:.2f}".format(float(value['retail_price']) * value['quantity'])
    except (ValueError, TypeError):
        return value


@register.filter
def first_word(value: str):
    try:
        return value.split(' ')[0]
    except (ValueError, TypeError):
        return value
