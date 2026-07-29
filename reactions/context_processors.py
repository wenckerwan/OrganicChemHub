from django.conf import settings
from .models import Message, NavItem


def app_version(request):
    ctx = {"APP_VERSION": getattr(settings, "APP_VERSION", "dev")}
    if request.user.is_authenticated:
        ctx["unread_message_count"] = Message.objects.filter(recipient=request.user, is_read=False).count()
    else:
        ctx["unread_message_count"] = 0
    return ctx


def nav_items(request):
    return {"nav_items": NavItem.objects.filter(is_active=True)}
