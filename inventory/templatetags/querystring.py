# inventory/templatetags/querystring.py
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring_without_sort(context):
    querydict = context["request"].GET.copy()
    querydict.pop("sort", None)
    return querydict.urlencode()
