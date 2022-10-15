from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    # print(dictionary)
    value = dictionary.get(key) if dictionary.get(key) is not None else ''
    return value

# return the item at index i from an indexable type like list
# if item not indexable then return ""


@register.filter
def index(indexable, i):
    # TODO: check if i is > lenght of indexable and return "" or error
    if indexable:
        return indexable[i]
    else:
        return ""

# function to return count of keys in the dictionary


@register.filter
def dict_len(dict):
    if dict:
        return len(dict)
    else:
        return 0
