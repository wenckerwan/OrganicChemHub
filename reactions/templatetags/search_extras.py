import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from reactions.services.search import build_querystring


register = template.Library()


@register.filter
def highlight_query(value, query):
    text = conditional_escape(value or "")
    query = conditional_escape(query or "")
    if not query:
        return text

    pattern = re.compile(re.escape(str(query)), re.IGNORECASE)

    def replace(match):
        return f'<mark class="search-highlight">{match.group(0)}</mark>'

    return mark_safe(pattern.sub(replace, str(text)))


@register.simple_tag(takes_context=True)
def querystring_replace(context, **updates):
    return build_querystring(context["request"].GET, **updates)
