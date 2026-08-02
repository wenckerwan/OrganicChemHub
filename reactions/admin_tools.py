from django.contrib import admin
from django.template.response import TemplateResponse

from .admin_forms import (
    MessageBroadcastForm,
    MessageCleanupForm,
    ReactionCsvImportForm,
    ResourceImportOrUploadForm,
)
from .models import GeneralReaction, LearningResource, NamedReaction, SyntheticRoute


def admin_context(request, title, **extra):
    context = admin.site.each_context(request)
    context.update({"title": title, **extra})
    return context


def dashboard_view(request):
    context = admin_context(
        request,
        "内容质量仪表盘",
        named_total=NamedReaction.objects.count(),
        general_total=GeneralReaction.objects.count(),
        routes_total=SyntheticRoute.objects.count(),
        resources_total=LearningResource.objects.count(),
    )
    return TemplateResponse(request, "admin/reactions/dashboard.html", context)


def reaction_import_view(request):
    context = admin_context(request, "CSV 导入", form=ReactionCsvImportForm())
    return TemplateResponse(request, "admin/reactions/import.html", context)


def image_maintenance_view(request):
    context = admin_context(
        request,
        "图片维护",
        named_missing_images=NamedReaction.objects.filter(equation_img="")[:50],
        general_missing_images=GeneralReaction.objects.filter(equation_img="")[:50],
    )
    return TemplateResponse(request, "admin/reactions/images.html", context)


def message_broadcast_view(request):
    context = admin_context(request, "站内消息群发", form=MessageBroadcastForm())
    return TemplateResponse(request, "admin/operations/message_send.html", context)


def message_cleanup_view(request):
    context = admin_context(request, "消息清理", form=MessageCleanupForm())
    return TemplateResponse(request, "admin/operations/message_cleanup.html", context)


def resource_upload_or_register_view(request):
    context = admin_context(request, "学习资料上传和登记", form=ResourceImportOrUploadForm())
    return TemplateResponse(request, "admin/resources/import_or_upload.html", context)