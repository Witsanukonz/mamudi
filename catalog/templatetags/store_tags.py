from django import template
register = template.Library()


@register.filter
def money(value):
    return f'{value:,.2f}'

