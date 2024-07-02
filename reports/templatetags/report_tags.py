from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Return the value of the specified key.
    """
    value = dictionary.get(key) if dictionary.get(key) is not None else ''
    return value


@register.filter
def index(indexable, i):
    """
    Return the value of the specified key.
    """
    if indexable:
        return indexable[i]
    else:
        return ""

@register.filter
def dict_len(dict):
    """
    Return the value of the specified key.
    """
    if dict:
        return len(dict)
    else:
        return 0

@register.filter
def get_item(dictionary, key):
    # print(dictionary)
    value = dictionary.get(key) if dictionary.get(key) is not None else ''
    return value