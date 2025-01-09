
from django import template

register = template.Library()


@register.filter
def at_index_i(list_like, i):
    """
    This allows retrieve the object at the specified index.
    This does not require a list, simply a container with
    indexing implemented.
    Args:
        list_like:
        i:

    Returns:

    """
    return list_like[i]
