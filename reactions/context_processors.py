from django.conf import settings
from types import SimpleNamespace

from .models import Message, NavItem


def app_version(request):
    ctx = {
        "APP_VERSION": getattr(settings, "APP_VERSION", "dev"),
        "ASSET_VERSION": getattr(settings, "ASSET_VERSION", getattr(settings, "APP_VERSION", "dev")),
    }
    if request.user.is_authenticated:
        ctx["unread_message_count"] = Message.objects.filter(recipient=request.user, is_read=False).count()
    else:
        ctx["unread_message_count"] = 0
    return ctx


def nav_items(request):
    return {"nav_items": [_normalized_nav_item(item) for item in NavItem.objects.filter(is_active=True)]}


def _normalized_nav_item(item):
    """Keep legacy database nav rows pointing at the current frontend libraries."""
    label = item.label
    url_name = item.url_name
    url_params = item.url_params
    if "常见" in label and "反应" in label:
        label = "常见有机反应"
        url_name = "general_reaction_list"
        url_params = ""
    elif url_name == "common_reaction_list":
        url_name = "general_reaction_list"
    return SimpleNamespace(label=label, url_name=url_name, url_params=url_params)
