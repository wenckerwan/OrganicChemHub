from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import FunctionalGroup, LearningResource, Reaction, ReactionType, RouteStep, SyntheticRoute, Tag


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
    actions = ("publish_selected", "archive_selected")
    date_hierarchy = "updated_at"
    list_display = ("name_zh", "name_en", "reaction_type", "status", "content_completeness_display", "updated_at")
    list_filter = ("status", "reaction_type", "tags", "functional_groups", "created_at", "updated_at")
    search_fields = ("name_zh", "name_en", "aliases", "condition", "summary", "exam_tips")
    prepopulated_fields = {"slug": ("name_en",)}
    filter_horizontal = ("tags", "functional_groups")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("基础信息", {"fields": ("name_zh", "name_en", "slug", "aliases", "reaction_type", "status")}),
        ("分类", {"fields": ("tags", "functional_groups")}),
        ("反应内容", {"fields": ("equation_smiles", "summary", "condition", "mechanism")}),
        ("学习资料", {"fields": ("scope", "limitations", "exam_tips", "reference")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="完整度")
    def content_completeness_display(self, obj):
        return obj.content_completeness()

    @admin.action(description="发布选中的完整反应")
    def publish_selected(self, request, queryset):
        self._publish_selected(request, queryset)

    @admin.action(description="归档选中的反应")
    def archive_selected(self, request, queryset):
        self._archive_selected(request, queryset)


class RouteStepInline(admin.TabularInline):
    model = RouteStep
    extra = 1
    fields = ("step_number", "title", "reactant_smiles", "product_smiles", "reagents", "condition", "yield_text")
    ordering = ("step_number",)


@admin.register(SyntheticRoute)
class SyntheticRouteAdmin(PublicationActionMixin, admin.ModelAdmin):
    actions = ("publish_selected", "archive_selected")
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
    search_fields = ("target_product", "target_smiles", "summary", "source")
    prepopulated_fields = {"slug": ("target_product",)}
    filter_horizontal = ("related_reactions",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (RouteStepInline,)
    fieldsets = (
        ("基础信息", {"fields": ("target_product", "target_smiles", "slug", "difficulty", "status")}),
        ("路线说明", {"fields": ("summary", "advantages", "disadvantages", "source", "related_reactions")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="步骤数")
    def step_count(self, obj):
        return obj.steps.count()

    @admin.display(description="完整度")
    def content_completeness_display(self, obj):
        return obj.content_completeness()

    @admin.action(description="发布选中的完整路线")
    def publish_selected(self, request, queryset):
        self._publish_selected(request, queryset)

    @admin.action(description="归档选中的路线")
    def archive_selected(self, request, queryset):
        self._archive_selected(request, queryset)


@admin.register(RouteStep)
class RouteStepAdmin(admin.ModelAdmin):
    list_display = ("route", "step_number", "title", "yield_text")
    list_filter = ("route", "related_reactions")
    search_fields = ("route__target_product", "title", "reagents", "condition", "note")
    filter_horizontal = ("related_reactions",)


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "year", "file_type", "size_label", "has_answer", "status", "updated_at")
    list_filter = ("status", "category", "file_type", "has_answer", "year", "source_folder")
    search_fields = ("title", "relative_path", "local_path", "source_folder")
    readonly_fields = ("created_at", "updated_at", "size_label")
    date_hierarchy = "updated_at"
    actions = ("publish_selected", "archive_selected")
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
