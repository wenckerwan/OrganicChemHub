import csv
import io

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.utils import timezone

from .admin_forms import (
    MessageBroadcastForm,
    MessageCleanupForm,
    ReactionCsvImportForm,
    ResourceImportOrUploadForm,
)
from .models import GeneralReaction, LearningResource, Message, NamedReaction, OpLog, PublishStatus, SyntheticRoute
from .services.publication import publication_ready_count


REQUIRED_IMPORT_COLUMNS = ["name_zh", "name_en", "slug", "summary", "condition", "exam_tips", "reference", "status"]
IMPORT_FIELDS = [
    "name_zh",
    "name_en",
    "slug",
    "aliases",
    "summary",
    "condition",
    "mechanism",
    "exam_tips",
    "scope",
    "limitations",
    "reference",
    "equation_img",
    "mechanism_img",
    "thumbnail_img",
    "status",
]


def admin_context(request, title, **extra):
    context = admin.site.each_context(request)
    context.update({"title": title, **extra})
    return context


def reaction_model_for_target(target):
    return NamedReaction if target == "named" else GeneralReaction


def reaction_quality_stats(model):
    queryset = model.objects.all()
    return {
        "total": queryset.count(),
        "published": queryset.filter(status=PublishStatus.PUBLISHED).count(),
        "drafts": queryset.filter(status=PublishStatus.DRAFT).count(),
        "archived": queryset.filter(status=PublishStatus.ARCHIVED).count(),
        "publish_ready": publication_ready_count(model),
        "missing_equation": queryset.filter(equation_img="").count(),
        "missing_thumbnail": queryset.filter(thumbnail_img="").count(),
        "missing_exam_tips": queryset.filter(exam_tips="").count(),
        "missing_condition": queryset.filter(condition="").count(),
        "category_distribution": queryset.values("category__name").annotate(count=Count("id")).order_by("-count"),
    }


def import_reactions_from_csv(uploaded_file, target, mode):
    model = reaction_model_for_target(target)
    decoded = uploaded_file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    result = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    missing_columns = [column for column in REQUIRED_IMPORT_COLUMNS if column not in (reader.fieldnames or [])]
    if missing_columns:
        result["errors"].append(f"缺少字段：{', '.join(missing_columns)}")
        result["skipped"] += 1
        return result

    for line_number, row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue

        row_errors = [column for column in REQUIRED_IMPORT_COLUMNS if not (row.get(column) or "").strip()]
        if row_errors:
            result["skipped"] += 1
            result["errors"].append(f"第 {line_number} 行缺少字段：{', '.join(row_errors)}")
            continue

        lookup = model.objects.filter(name_zh=row["name_zh"].strip(), name_en=row["name_en"].strip()).first()
        if lookup and mode == "create":
            result["skipped"] += 1
            continue

        obj = lookup or model()
        for field in IMPORT_FIELDS:
            if field in row and row[field] is not None:
                setattr(obj, field, row[field].strip())

        try:
            obj.full_clean()
        except Exception as exc:
            result["skipped"] += 1
            result["errors"].append(f"第 {line_number} 行校验失败：{exc}")
            continue

        obj.save()
        if lookup:
            result["updated"] += 1
        else:
            result["created"] += 1

    return result


def dashboard_view(request):
    named_stats = reaction_quality_stats(NamedReaction)
    general_stats = reaction_quality_stats(GeneralReaction)
    route_total = SyntheticRoute.objects.count()
    routes_missing_steps = sum(1 for route in SyntheticRoute.objects.all() if not route.steps.exists())
    context = admin_context(
        request,
        "内容质量仪表盘",
        named_stats=named_stats,
        general_stats=general_stats,
        named_total=named_stats["total"],
        general_total=general_stats["total"],
        routes_total=route_total,
        routes_missing_steps=routes_missing_steps,
        resources_total=LearningResource.objects.count(),
    )
    return TemplateResponse(request, "admin/reactions/dashboard.html", context)


def reaction_import_view(request):
    result = None
    if request.method == "POST":
        form = ReactionCsvImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = import_reactions_from_csv(
                form.cleaned_data["csv_file"],
                form.cleaned_data["target"],
                form.cleaned_data["mode"],
            )
            messages.success(
                request,
                f"CSV 导入完成：新增 {result['created']}，更新 {result['updated']}，跳过 {result['skipped']}。",
            )
    else:
        form = ReactionCsvImportForm()
    context = admin_context(request, "CSV 导入", form=form, result=result)
    return TemplateResponse(request, "admin/reactions/import.html", context)


def image_maintenance_view(request):
    required_missing = Q(equation_img="") | Q(thumbnail_img="")
    context = admin_context(
        request,
        "图片维护",
        named_missing_images=NamedReaction.objects.filter(required_missing)[:50],
        general_missing_images=GeneralReaction.objects.filter(required_missing)[:50],
        named_missing_mechanism=NamedReaction.objects.filter(mechanism_img="")[:50],
        general_missing_mechanism=GeneralReaction.objects.filter(mechanism_img="")[:50],
    )
    return TemplateResponse(request, "admin/reactions/images.html", context)


def message_broadcast_view(request):
    result = None
    if request.method == "POST":
        form = MessageBroadcastForm(request.POST)
        if form.is_valid():
            users = User.objects.all()
            Message.objects.bulk_create(
                [
                    Message(
                        recipient=user,
                        msg_type=form.cleaned_data["msg_type"],
                        title=form.cleaned_data["title"],
                        content=form.cleaned_data["content"],
                    )
                    for user in users
                ]
            )
            result = {"sent": users.count()}
            OpLog.objects.create(
                user=request.user,
                action="broadcast_message",
                model_name="Message",
                object_repr=form.cleaned_data["title"],
                detail=f"已发送 {result['sent']} 条站内消息。",
            )
            messages.success(request, f"已发送 {result['sent']} 条站内消息。")
    else:
        form = MessageBroadcastForm()
    context = admin_context(request, "站内消息群发", form=form, result=result)
    return TemplateResponse(request, "admin/operations/message_send.html", context)


def message_cleanup_view(request):
    result = None
    if request.method == "POST":
        form = MessageCleanupForm(request.POST)
        if form.is_valid() and form.cleaned_data["confirm"]:
            months = int(form.cleaned_data["older_than"])
            cutoff = timezone.now() - timezone.timedelta(days=months * 30)
            queryset = Message.objects.filter(created_at__lt=cutoff)
            if form.cleaned_data["read_only"]:
                queryset = queryset.filter(is_read=True)
            deleted_count = queryset.count()
            queryset.delete()
            result = {"deleted": deleted_count}
            OpLog.objects.create(
                user=request.user,
                action="cleanup_messages",
                model_name="Message",
                object_repr=f"{months} months",
                detail=f"已清理 {deleted_count} 条站内消息。",
            )
            messages.success(request, f"已清理 {deleted_count} 条站内消息。")
    else:
        form = MessageCleanupForm()
    context = admin_context(request, "消息清理", form=form, result=result)
    return TemplateResponse(request, "admin/operations/message_cleanup.html", context)


def resource_upload_or_register_view(request):
    context = admin_context(request, "学习资料上传和登记", form=ResourceImportOrUploadForm())
    return TemplateResponse(request, "admin/resources/import_or_upload.html", context)
