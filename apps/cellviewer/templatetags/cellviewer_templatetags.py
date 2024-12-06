
from django import template

register = template.Library()


@register.filter
def at_index_i(list_like, i):
    return list_like[i]
