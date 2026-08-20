import csv
import io
import json

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone

from .admin_forms import (
    MessageBroadcastForm,
    MessageCleanupForm,
    ReactionCsvImportForm,
    ResourceImportOrUploadForm,
)
from .models import ContentBatch, GeneralReaction, LearningResource, Message, NamedReaction, PublishStatus, ReactionImage, SyntheticRoute, VisitCounter
from .services import audit
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
    prefetched_queryset = queryset.prefetch_related("images")
    counters = {
        counter.key: counter
        for counter in VisitCounter.objects.filter(
            key__in=[VisitCounter.key_for_object(obj) for obj in queryset]
        )
    }
    high_traffic_incomplete = []
    for obj in prefetched_queryset:
        missing = obj.get_publication_missing_fields()
        counter = counters.get(VisitCounter.key_for_object(obj))
        if missing and counter and counter.total_count:
            high_traffic_incomplete.append({
                "name": str(obj),
                "url": obj.get_absolute_url(),
                "total": counter.total_count,
                "today": counter.today_count,
                "missing": obj.missing_fields_display(),
            })
    high_traffic_incomplete.sort(key=lambda item: item["total"], reverse=True)
    image_queryset = ReactionImage.objects.filter(content_type__model=model._meta.model_name)
    return {
        "total": queryset.count(),
        "published": queryset.filter(status=PublishStatus.PUBLISHED).count(),
        "drafts": queryset.filter(status=PublishStatus.DRAFT).count(),
        "archived": queryset.filter(status=PublishStatus.ARCHIVED).count(),
        "publish_ready": publication_ready_count(model),
        "missing_equation": sum(1 for obj in prefetched_queryset if "equation_img" in obj.get_publication_missing_fields()),
        "missing_thumbnail": sum(1 for obj in prefetched_queryset if "thumbnail_img" in obj.get_publication_missing_fields()),
        "missing_exam_tips": sum(1 for obj in prefetched_queryset if "exam_tips" in obj.get_publication_missing_fields()),
        "missing_condition": sum(1 for obj in prefetched_queryset if "condition" in obj.get_publication_missing_fields()),
        "review_pending": image_queryset.filter(review_status=ReactionImage.ReviewStatus.PENDING).count(),
        "review_approved": image_queryset.filter(review_status=ReactionImage.ReviewStatus.APPROVED).count(),
        "review_redraw": image_queryset.filter(review_status=ReactionImage.ReviewStatus.REDRAW).count(),
        "high_traffic_incomplete": high_traffic_incomplete[:10],
        "category_distribution": queryset.values("category__name").annotate(count=Count("id")).order_by("-count"),
    }


def import_reactions_from_csv(uploaded_file, target, mode):
    model = reaction_model_for_target(target)
    decoded = uploaded_file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    result = {"created": 0, "updated": 0, "skipped": 0, "errors": [], "names": []}

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
            result["errors"].append({
                "line": line_number,
                "fields": row_errors,
                "raw": (row.get("name_zh") or "")[:50],
                "reason": "缺少字段",
            })
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
                result["errors"].append({
                    "line": line_number,
                    "fields": [],
                    "raw": (row.get("name_zh") or "")[:50],
                    "reason": str(exc),
                })
                continue

        obj.save()
        result["names"].append(str(obj))
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
            target_label = "人名反应" if form.cleaned_data["target"] == "named" else "常见有机反应"
            if result["created"] or result["updated"]:
                audit.log_operation(
                    request.user,
                    action="csv_import",
                    model_name=form.cleaned_data["target"],
                    object_repr=f"{target_label} CSV 导入",
                    detail=f"新增 {result['created']}，更新 {result['updated']}，跳过 {result['skipped']}。",
                    ip=request.META.get("REMOTE_ADDR"),
                )
                audit.record_batch(
                    kind=ContentBatch.Kind.IMPORT,
                    operator=request.user,
                    summary="CSV 导入",
                    objects=result["names"],
                    detail={
                        "target": form.cleaned_data["target"],
                        "created": result["created"],
                        "updated": result["updated"],
                        "skipped": result["skipped"],
                    },
                )
            messages.success(
                request,
                f"CSV 导入完成：新增 {result['created']}，更新 {result['updated']}，跳过 {result['skipped']}。",
            )
    else:
        form = ReactionCsvImportForm()
    context = admin_context(request, "CSV 导入", form=form, result=result)
    return TemplateResponse(request, "admin/reactions/import.html", context)


def import_error_download_view(request):
    """Download structured import errors as CSV for re-import after fixing."""
    if request.method != "POST":
        return HttpResponse(status=405)
    errors = json.loads(request.POST.get("errors", "[]"))

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = "attachment; filename=import_errors.csv"
    writer = csv.writer(response)
    writer.writerow(["行号", "错误字段", "原始值", "建议修复"])
    for err in errors:
        writer.writerow([
            err.get("line", ""),
            "、".join(err.get("fields", [])),
            err.get("raw", ""),
            err.get("reason", ""),
        ])
    return response


def image_maintenance_view(request):
    named_with_images = NamedReaction.objects.prefetch_related("images")
    general_with_images = GeneralReaction.objects.prefetch_related("images")
    context = admin_context(
        request,
        "图片维护",
        named_missing_images=[
            obj for obj in named_with_images if {"equation_img", "thumbnail_img"} & set(obj.get_publication_missing_fields())
        ][:50],
        general_missing_images=[
            obj for obj in general_with_images if {"equation_img", "thumbnail_img"} & set(obj.get_publication_missing_fields())
        ][:50],
        named_missing_mechanism=[
            obj for obj in named_with_images if not obj.mechanism_img and not obj.mechanism_gallery_images.exists()
        ][:50],
        general_missing_mechanism=[
            obj for obj in general_with_images if not obj.mechanism_img and not obj.mechanism_gallery_images.exists()
        ][:50],
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
            audit.log_operation(
                request.user,
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
            audit.log_operation(
                request.user,
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
