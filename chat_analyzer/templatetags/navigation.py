from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active(context, url_name):
    """returns 'active' if the current url matches with the given url name"""
    request = context.get('request')
    if request and request.resolver_match and request.resolver_match.url_name == url_name:
        return 'active'
    return ''

