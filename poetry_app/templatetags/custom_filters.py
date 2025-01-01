from django import template
from itertools import zip_longest

register = template.Library()

@register.filter
def zip_longest_filter(a, b):
    """
    Zips two iterables using itertools.zip_longest.
    Pads the shorter iterable with None.
    """
    return zip_longest(a, b)

@register.filter
def get_item(dictionary, key):
    """
    Retrieves the value from a dictionary for the given key.
    Returns None if the dictionary is None or the key does not exist.
    """
    if dictionary:
        return dictionary.get(key)
    return None
