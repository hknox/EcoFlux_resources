from django import template

register = template.Library()


@register.filter
def get_field_display(obj, field_name):
    """Custom filter to access dynamic attributes"""
    return getattr(obj, field_name, "")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")
