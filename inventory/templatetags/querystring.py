# inventory/templatetags/querystring.py
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring_without_sort(context):
    request = context["request"]
    querydict = request.GET.copy()
    querydict.pop("sort", None)
    return querydict.urlencode()
