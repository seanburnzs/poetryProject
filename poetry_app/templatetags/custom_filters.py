from django import template
from itertools import zip_longest
import bleach
from django import template

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

@register.filter
def remove_inline_color(html_content):
    # Only allow safe tags, disallow style attributes
    return bleach.clean(
        html_content,
        tags=bleach.ALLOWED_TAGS + ['p', 'span', 'br'],
        attributes={},
        styles=[],  # Disallow all inline styles
        strip=True
    )