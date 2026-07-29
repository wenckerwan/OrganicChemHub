import csv

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from django.template.response import TemplateResponse

from .models import Announcement, Feedback, FunctionalGroup, LearningResource, Reaction, ReactionType, RouteStep, SyntheticRoute, Tag


admin.site.site_header = "OrganicChemHub 管理后台"
admin.site.site_title = "OrganicChemHub"
admin.site.index_title = "有机化学资料库"


class PublicationActionMixin:
    def _publish_selected(self, request, queryset):
        published_count = 0
        skipped_items = []

        for item in queryset:
            item.status = item.Status.PUBLISHED
            try:
                item.full_clean()
            except ValidationError:
                skipped_items.append(str(item))
                continue

            item.save(update_fields=["status", "updated_at"])
            published_count += 1

        if published_count:
            self.message_user(request, f"已发布 {published_count} 条内容。", fail_silently=True)
        if skipped_items:
            preview = "、".join(skipped_items[:5])
            self.message_user(
                request,
                f"已跳过 {len(skipped_items)} 条不完整内容：{preview}",
                level="warning",
                fail_silently=True,
            )

    def _archive_selected(self, request, queryset):
        archived_count = queryset.update(status=queryset.model.Status.ARCHIVED)
        self.message_user(request, f"已归档 {archived_count} 条内容。", fail_silently=True)


@admin.register(ReactionType)
class ReactionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(FunctionalGroup)
class FunctionalGroupAdmin(admin.ModelAdmin):
    list_display = ("name_zh", "name_en", "smarts")
    search_fields = ("name_zh", "name_en", "smarts", "description")


@admin.register(Reaction)
class ReactionAdmin(PublicationActionMixin, admin.ModelAdmin):
    actions = ("publish_selected", "archive_selected", "export_selected_as_csv")
    date_hierarchy = "updated_at"
    list_display = (
        "name_zh",
        "name_en",
        "reaction_type",
        "status",
        "admin_thumbnail",
        "structure_image_status",
        "content_completeness_display",
        "updated_at",
    )
    list_filter = ("status", "reaction_type", "tags", "functional_groups", "created_at", "updated_at")
    search_fields = ("name_zh", "name_en", "aliases", "condition", "summary", "exam_tips")
    prepopulated_fields = {"slug": ("name_en",)}
    filter_horizontal = ("tags", "functional_groups")
    readonly_fields = (
        "equation_img_preview",
        "mechanism_img_preview",
        "thumbnail_img_preview",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("基础信息", {"fields": ("name_zh", "name_en", "slug", "aliases", "reaction_type", "status")}),
        ("分类", {"fields": ("tags", "functional_groups")}),
        (
            "反应方程式图片",
            {
                "description": "上传反应的 SVG 或 PNG 图片。如不上传，前台将显示暂无图片。",
                "fields": (
                    "equation_img_preview",
                    "equation_img",
                )
            },
        ),
        (
            "反应机理图片",
            {
                "fields": (
                    "mechanism_img_preview",
                    "mechanism_img",
                )
            },
        ),
        (
            "缩略图",
            {
                "fields": (
                    "thumbnail_img_preview",
                    "thumbnail_img",
                )
            },
        ),
        ("反应内容", {"fields": ("summary", "condition", "mechanism")}),
        ("学习资料", {"fields": ("scope", "limitations", "exam_tips", "reference")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="完整度")
    def content_completeness_display(self, obj):
        return obj.content_completeness()

    @admin.display(description="结构图")
    def structure_image_status(self, obj):
        return "已配置" if obj.get_equation_img_src() else "待补"

    @admin.display(description="缩略图")
    def admin_thumbnail(self, obj):
        src = obj.get_thumbnail_img_src() or obj.get_equation_img_src()
        if not src:
            return "—"
        return format_html(
            '<img src="{}" alt="缩略图" style="width:60px;height:60px;object-fit:contain;background:#fff;border:1px solid #ddd;border-radius:4px;">',
            src,
        )

    @admin.display(description="反应方程式图片预览")
    def equation_img_preview(self, obj):
        if not obj or not obj.get_equation_img_src():
            return "暂未上传"
        return format_html(
            '<img src="{}" alt="方程式预览" style="max-width:420px;max-height:220px;background:#fff;border:1px solid #d8dee8;border-radius:8px;padding:8px;">',
            obj.get_equation_img_src(),
        )

    @admin.display(description="反应机理图片预览")
    def mechanism_img_preview(self, obj):
        if not obj or not obj.get_mechanism_img_src():
            return "暂未上传"
        return format_html(
            '<img src="{}" alt="机理预览" style="max-width:420px;max-height:220px;background:#fff;border:1px solid #d8dee8;border-radius:8px;padding:8px;">',
            obj.get_mechanism_img_src(),
        )

    @admin.display(description="缩略图预览")
    def thumbnail_img_preview(self, obj):
        if not obj or not obj.get_thumbnail_img_src():
            return "暂未上传"
        return format_html(
            '<img src="{}" alt="缩略图预览" style="max-width:200px;max-height:120px;background:#fff;border:1px solid #d8dee8;border-radius:4px;padding:4px;">',
            obj.get_thumbnail_img_src(),
        )

    @admin.action(description="发布选中的完整反应")
    def publish_selected(self, request, queryset):
        self._publish_selected(request, queryset)

    @admin.action(description="归档选中的反应")
    def archive_selected(self, request, queryset):
        self._archive_selected(request, queryset)

    @admin.display(description="图片状态")
    def image_status_tag(self, obj):
        if obj.get_equation_img_src():
            return format_html('<span style="color:#0f766e;font-weight:700;">✔</span>')
        return format_html('<span style="color:#a15c38;font-weight:700;">✗</span>')

    @admin.action(description="导出选中的反应为 CSV")
    def export_selected_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = "attachment; filename=reactions_export.csv"

        writer = csv.writer(response)
        writer.writerow([
            "name_zh", "name_en", "slug", "reaction_type",
            "aliases", "summary", "condition", "mechanism",
            "scope", "limitations", "exam_tips", "reference",
            "status", "has_image",
        ])

        for rxn in queryset.select_related("reaction_type"):
            writer.writerow([
                rxn.name_zh, rxn.name_en, rxn.slug,
                rxn.reaction_type.name if rxn.reaction_type else "",
                rxn.aliases, rxn.summary, rxn.condition,
                rxn.mechanism, rxn.scope,
                rxn.limitations, rxn.exam_tips, rxn.reference,
                rxn.status,
                "Y" if rxn.get_equation_img_src() else "",
            ])

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.dashboard_view, name="reactions_dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        now = timezone.now()

        total = Reaction.objects.count()
        published = Reaction.objects.filter(status=Reaction.Status.PUBLISHED).count()
        drafts = Reaction.objects.filter(status=Reaction.Status.DRAFT).count()
        archived = Reaction.objects.filter(status=Reaction.Status.ARCHIVED).count()

        # Quality checks
        missing_image = sum(1 for r in Reaction.objects.all() if not r.get_equation_img_src())
        missing_summary = Reaction.objects.filter(summary="").count()
        missing_condition = Reaction.objects.filter(condition="").count()
        missing_reference = Reaction.objects.filter(reference="").count()
        missing_type = Reaction.objects.filter(reaction_type__isnull=True).count()

        recent_reactions = Reaction.objects.order_by("-updated_at")[:10]

        routes_total = SyntheticRoute.objects.count()
        resources_total = LearningResource.objects.count()

        context = {
            **admin.site.each_context(request),
            "title": "内容质量仪表盘",
            "total": total,
            "published": published,
            "drafts": drafts,
            "archived": archived,
            "missing_image": missing_image,
            "missing_summary": missing_summary,
            "missing_condition": missing_condition,
            "missing_reference": missing_reference,
            "missing_type": missing_type,
            "recent_reactions": recent_reactions,
            "routes_total": routes_total,
            "resources_total": resources_total,
        }
        return TemplateResponse(request, "admin/reactions/dashboard.html", context)


class RouteStepInline(admin.TabularInline):
    model = RouteStep
    extra = 1
    fields = (
        "step_number",
        "title",
        "reactant_structure_image",
        "reactant_structure_image_url",
        "product_structure_image",
        "product_structure_image_url",
        "structure_image_caption",
        "reagents",
        "condition",
        "yield_text",
    )
    ordering = ("step_number",)


@admin.register(SyntheticRoute)
class SyntheticRouteAdmin(PublicationActionMixin, admin.ModelAdmin):
    actions = ("publish_selected", "archive_selected", "export_selected_as_csv")
    date_hierarchy = "updated_at"
    list_display = (
        "target_product",
        "difficulty",
        "status",
        "step_count",
        "content_completeness_display",
        "source",
        "updated_at",
    )
    list_filter = ("status", "difficulty", "related_reactions", "created_at", "updated_at")
    search_fields = ("target_product", "summary", "source")
    prepopulated_fields = {"slug": ("target_product",)}
    filter_horizontal = ("related_reactions",)
    readonly_fields = ("target_structure_image_preview", "created_at", "updated_at")
    inlines = (RouteStepInline,)
    fieldsets = (
        ("基础信息", {"fields": ("target_product", "slug", "difficulty", "status")}),
        (
            "目标产物结构式",
            {
                "description": "上传结构式的 SVG 或 PNG；有图床路径则填 URL。",
                "fields": (
                    "target_structure_image_preview",
                    "target_structure_image",
                    "target_structure_image_url",
                    "target_structure_image_caption",
                )
            },
        ),
        ("路线说明", {"fields": ("summary", "advantages", "disadvantages", "source", "related_reactions")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="步骤数")
    def step_count(self, obj):
        return obj.steps.count()

    @admin.display(description="完整度")
    def content_completeness_display(self, obj):
        return obj.content_completeness()

    @admin.display(description="目标产物结构式预览")
    def target_structure_image_preview(self, obj):
        if not obj or not obj.get_target_structure_image_src():
            return "暂无目标产物结构式图片"
        return format_html(
            '<img src="{}" alt="目标产物结构式预览" style="max-width: 420px; max-height: 220px; background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 8px;">',
            obj.get_target_structure_image_src(),
        )

    @admin.action(description="发布选中的完整路线")
    def publish_selected(self, request, queryset):
        self._publish_selected(request, queryset)

    @admin.action(description="归档选中的路线")
    def archive_selected(self, request, queryset):
        self._archive_selected(request, queryset)

    @admin.action(description="导出选中的路线为 CSV")
    def export_selected_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = "attachment; filename=routes_export.csv"
        writer = csv.writer(response)
        writer.writerow(["target_product", "slug", "difficulty", "summary", "advantages", "disadvantages", "source", "step_count", "status"])
        for obj in queryset:
            writer.writerow([
                obj.target_product, obj.slug, obj.difficulty, obj.summary,
                obj.advantages, obj.disadvantages, obj.source,
                obj.steps.count(), obj.status,
            ])
        return response


@admin.register(RouteStep)
class RouteStepAdmin(admin.ModelAdmin):
    list_display = ("route", "step_number", "title", "yield_text")
    list_filter = ("route", "related_reactions")
    search_fields = ("route__target_product", "title", "reagents", "condition", "note")
    filter_horizontal = ("related_reactions",)
    readonly_fields = ("reactant_structure_image_preview", "product_structure_image_preview")
    fieldsets = (
        ("基础信息", {"fields": ("route", "step_number", "title", "related_reactions")}),
        (
            "反应物与产物结构式",
            {
                "fields": (
                    "reactant_structure_image_preview",
                    "reactant_structure_image",
                    "reactant_structure_image_url",
                    "product_structure_image_preview",
                    "product_structure_image",
                    "product_structure_image_url",
                    "structure_image_caption",
                )
            },
        ),
        ("反应条件", {"fields": ("reagents", "condition", "yield_text", "note")}),
    )

    @admin.display(description="反应物结构式预览")
    def reactant_structure_image_preview(self, obj):
        if not obj or not obj.get_reactant_structure_image_src():
            return "暂无反应物结构式图片"
        return format_html(
            '<img src="{}" alt="反应物结构式预览" style="max-width: 420px; max-height: 220px; background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 8px;">',
            obj.get_reactant_structure_image_src(),
        )

    @admin.display(description="产物结构式预览")
    def product_structure_image_preview(self, obj):
        if not obj or not obj.get_product_structure_image_src():
            return "暂无产物结构式图片"
        return format_html(
            '<img src="{}" alt="产物结构式预览" style="max-width: 420px; max-height: 220px; background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 8px;">',
            obj.get_product_structure_image_src(),
        )


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "year", "file_type", "size_label", "has_answer", "status", "updated_at")
    list_filter = ("status", "category", "file_type", "has_answer", "year", "source_folder")
    search_fields = ("title", "relative_path", "local_path", "source_folder")
    readonly_fields = ("created_at", "updated_at", "size_label")
    date_hierarchy = "updated_at"
    actions = ("publish_selected", "archive_selected", "export_selected_as_csv")
    fieldsets = (
        ("基础信息", {"fields": ("title", "category", "year", "status", "has_answer")}),
        ("文件信息", {"fields": ("file_type", "size_bytes", "size_label", "relative_path", "local_path", "source_folder")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="文件大小")
    def size_label(self, obj):
        return obj.size_label()

    @admin.action(description="发布选中的资料索引")
    def publish_selected(self, request, queryset):
        updated_count = queryset.update(status=LearningResource.Status.PUBLISHED)
        self.message_user(request, f"已发布 {updated_count} 条资料索引。", fail_silently=True)

    @admin.action(description="归档选中的资料索引")
    def archive_selected(self, request, queryset):
        updated_count = queryset.update(status=LearningResource.Status.ARCHIVED)
        self.message_user(request, f"已归档 {updated_count} 条资料索引。", fail_silently=True)

    @admin.action(description="导出选中的资料为 CSV")
    def export_selected_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = "attachment; filename=learning_resources_export.csv"
        writer = csv.writer(response)
        writer.writerow(["title", "category", "year", "file_type", "size_bytes", "has_answer", "status"])
        for obj in queryset:
            writer.writerow([obj.title, obj.category, obj.year, obj.file_type, obj.size_bytes, obj.has_answer, obj.status])
        return response


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "content")
    fieldsets = (
        ("公告内容", {"fields": ("title", "content", "is_active")}),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "short_content", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "content")
    readonly_fields = ("name", "email", "content", "created_at")
    actions = ("mark_as_read",)

    @admin.display(description="反馈内容")
    def short_content(self, obj):
        return obj.content[:80] + ("..." if len(obj.content) > 80 else "")

    @admin.action(description="标记为已读")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"已将 {updated} 条反馈标记为已读。")
