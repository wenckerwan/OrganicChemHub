import uuid

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.deconstruct import deconstructible


@deconstructible
class ReactionImageUploadTo:
    """Upload-to callable that renames uploaded images per v0.5 convention.

    Produces paths like: media/reaction_images/reaction_{slug}_equation.svg
    """
    def __init__(self, suffix):
        self.suffix = suffix

    def __call__(self, instance, filename):
        slug = getattr(instance, "slug", None) or str(instance.pk or "new")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "svg"
        return f"reaction_images/reaction_{slug}_{self.suffix}.{ext}"

    def __eq__(self, other):
        return isinstance(other, ReactionImageUploadTo) and self.suffix == other.suffix

    def __hash__(self):
        return hash(self.suffix)


@deconstructible
class ReactionGalleryImageUploadTo:
    def __call__(self, instance, filename):
        content = getattr(instance, "content_object", None)
        slug = getattr(content, "slug", None) or str(getattr(instance, "object_id", None) or "new")
        section = getattr(instance, "section", "image") or "image"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "svg"
        token = uuid.uuid4().hex[:10]
        return f"reaction_images/reaction_{slug}_{section}_{token}.{ext}"

    def __eq__(self, other):
        return isinstance(other, ReactionGalleryImageUploadTo)

    def __hash__(self):
        return hash("ReactionGalleryImageUploadTo")


def first_image_source(uploaded_file, image_url):
    if uploaded_file:
        return uploaded_file.url
    return image_url.strip()


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=PublishStatus.PUBLISHED)


class PublishedManager(models.Manager):
    def get_queryset(self):
        return PublishedQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()


class PublishedOnlyManager(PublishedManager):
    def get_queryset(self):
        return super().get_queryset().published()


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    PUBLISHED = "published", "已发布"
    ARCHIVED = "archived", "已归档"


class ReactionType(models.Model):
    name = models.CharField("类型名称", max_length=50, unique=True)
    slug = models.SlugField("URL 标识", max_length=80, unique=True)
    description = models.TextField("类型描述", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "反应类型"
        verbose_name_plural = "反应类型"

    def __str__(self):
        return self.name


class NamedReactionCategory(models.Model):
    name = models.CharField("名称", max_length=80, unique=True)
    slug = models.SlugField("URL 标识", max_length=100, unique=True)
    description = models.TextField("描述", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "人名反应分类"
        verbose_name_plural = "人名反应分类"

    def __str__(self):
        return self.name


class GeneralReactionCategory(models.Model):
    name = models.CharField("名称", max_length=80, unique=True)
    slug = models.SlugField("URL 标识", max_length=100, unique=True)
    description = models.TextField("描述", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "常见有机反应分类"
        verbose_name_plural = "常见有机反应分类"

    def __str__(self):
        return self.name

class NavItem(models.Model):
    label = models.CharField("菜单名称", max_length=50)
    url_name = models.CharField("URL 名称", max_length=100, help_text="Django URL name，例如 reaction_list")
    url_params = models.CharField("URL 参数", max_length=200, blank=True, help_text="查询参数，例如 ?tag=exam-high-frequency")
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("前台显示", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "pk"]
        verbose_name = "导航菜单"
        verbose_name_plural = "导航菜单"

    def __str__(self):
        return self.label


class Tag(models.Model):
    name = models.CharField("标签名称", max_length=50, unique=True)
    slug = models.SlugField("URL 标识", max_length=80, unique=True)
    description = models.TextField("标签描述", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "标签"
        verbose_name_plural = "标签"

    def __str__(self):
        return self.name


class FunctionalGroup(models.Model):
    name_zh = models.CharField("中文名", max_length=50, unique=True)
    name_en = models.CharField("英文名", max_length=80, blank=True)
    smarts = models.CharField("SMARTS", max_length=200, blank=True)
    description = models.TextField("说明", blank=True)

    class Meta:
        ordering = ["name_zh"]
        verbose_name = "官能团"
        verbose_name_plural = "官能团"

    def __str__(self):
        return self.name_zh


class Reaction(models.Model):
    Status = PublishStatus
    PUBLICATION_REQUIRED_FIELDS = {
        "summary": "简要说明",
        "condition": "反应条件",
        "reference": "参考来源",
    }

    name_zh = models.CharField("中文名称", max_length=100)
    name_en = models.CharField("英文名称", max_length=100)
    slug = models.SlugField("URL 标识", max_length=120, unique=True)
    aliases = models.CharField("别名", max_length=300, blank=True)
    reaction_type = models.ForeignKey(
        ReactionType,
        verbose_name="反应类型",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reactions",
    )
    tags = models.ManyToManyField(Tag, verbose_name="标签", blank=True, related_name="reactions")
    functional_groups = models.ManyToManyField(
        FunctionalGroup,
        verbose_name="相关官能团",
        blank=True,
        related_name="reactions",
    )
    is_common = models.BooleanField("常见反应", default=False, help_text="勾选后该反应出现在常见反应列表中")
    equation_img = models.FileField(
        "反应方程式图片", upload_to=ReactionImageUploadTo("equation"), blank=True,
        help_text="上传反应方程式的 SVG 或 PNG 图片"
    )
    mechanism_img = models.FileField(
        "反应机理图片", upload_to=ReactionImageUploadTo("mechanism"), blank=True,
        help_text="上传机理图的 SVG 或 PNG 图片"
    )
    thumbnail_img = models.FileField(
        "缩略图", upload_to=ReactionImageUploadTo("thumbnail"), blank=True,
        help_text="上传缩略图，用于列表页和卡片展示"
    )
    structure_image = models.FileField("结构式图片", upload_to="reaction_structures/", blank=True)
    structure_image_url = models.CharField("结构式图片 URL", max_length=500, blank=True)
    structure_image_caption = models.CharField("结构式图片说明", max_length=200, blank=True)
    summary = models.TextField("简要说明", blank=True)
    condition = models.TextField("反应条件", blank=True)
    mechanism = models.TextField("机理说明", blank=True)
    scope = models.TextField("适用范围", blank=True)
    limitations = models.TextField("限制与注意事项", blank=True)
    exam_tips = models.TextField("考点与易错点", blank=True)
    reference = models.TextField("参考来源", blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = PublishedManager()
    published = PublishedOnlyManager()

    class Meta:
        ordering = ["name_en", "name_zh"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["name_zh"]),
            models.Index(fields=["name_en"]),
        ]
        verbose_name = "人名反应"
        verbose_name_plural = "人名反应"

    def __str__(self):
        return self.name_zh

    def get_absolute_url(self):
        return reverse("reaction_detail", kwargs={"slug": self.slug})

    def get_structure_image_src(self):
        return first_image_source(self.structure_image, self.structure_image_url)

    def get_equation_img_src(self):
        return self.equation_img.url if self.equation_img else self.structure_image_url if self.structure_image_url.strip() else ""

    def get_mechanism_img_src(self):
        return self.mechanism_img.url if self.mechanism_img else ""

    def get_thumbnail_img_src(self):
        return self.thumbnail_img.url if self.thumbnail_img else self.get_equation_img_src()

    def get_publication_missing_fields(self):
        return [field for field in self.PUBLICATION_REQUIRED_FIELDS if not getattr(self, field, "").strip()]

    def content_completeness(self):
        total = len(self.PUBLICATION_REQUIRED_FIELDS)
        complete = total - len(self.get_publication_missing_fields())
        return f"{complete}/{total}"

    def clean(self):
        super().clean()
        if self.status != self.Status.PUBLISHED:
            return
        missing_fields = self.get_publication_missing_fields()
        if missing_fields:
            raise ValidationError(
                {field: f"发布前请填写{self.PUBLICATION_REQUIRED_FIELDS[field]}。" for field in missing_fields}
            )


class BaseReactionContent(models.Model):
    Status = PublishStatus
    REQUIRED_FIELDS = {
        "summary": "摘要",
        "condition": "反应条件",
        "exam_tips": "考研考点",
        "reference": "参考来源",
        "equation_img": "反应方程式图",
        "thumbnail_img": "缩略图",
    }

    name_zh = models.CharField("中文名", max_length=120)
    name_en = models.CharField("英文名", max_length=120, blank=True)
    aliases = models.CharField("别名", max_length=300, blank=True)
    slug = models.SlugField("URL 标识", max_length=140, unique=True)
    tags = models.ManyToManyField(Tag, verbose_name="标签", blank=True)
    functional_groups = models.ManyToManyField(FunctionalGroup, verbose_name="官能团", blank=True)
    summary = models.TextField("摘要", blank=True)
    condition = models.TextField("反应条件", blank=True)
    mechanism = models.TextField("机理描述", blank=True)
    exam_tips = models.TextField("考研考点", blank=True)
    scope = models.TextField("适用范围", blank=True)
    limitations = models.TextField("使用限制", blank=True)
    reference = models.TextField("参考来源", blank=True)
    equation_img = models.FileField("反应方程式图", upload_to=ReactionImageUploadTo("equation"), blank=True)
    mechanism_img = models.FileField("机理图", upload_to=ReactionImageUploadTo("mechanism"), blank=True)
    thumbnail_img = models.FileField("缩略图", upload_to=ReactionImageUploadTo("thumbnail"), blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = PublishedManager()
    published = PublishedOnlyManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name_zh

    def get_equation_img_src(self):
        return self.equation_img.url if self.equation_img else ""

    def get_mechanism_img_src(self):
        return self.mechanism_img.url if self.mechanism_img else ""

    def get_thumbnail_img_src(self):
        return self.thumbnail_img.url if self.thumbnail_img else self.get_equation_img_src()

    def gallery_images(self, section):
        return self.images.filter(section=section).order_by("sort_order", "pk")

    @property
    def equation_gallery_images(self):
        return self.gallery_images(ReactionImage.Section.EQUATION)

    @property
    def mechanism_gallery_images(self):
        return self.gallery_images(ReactionImage.Section.MECHANISM)

    @property
    def condition_gallery_images(self):
        return self.gallery_images(ReactionImage.Section.CONDITION)

    @property
    def mechanism_text_gallery_images(self):
        return self.gallery_images(ReactionImage.Section.MECHANISM_TEXT)

    @property
    def exam_tips_gallery_images(self):
        return self.gallery_images(ReactionImage.Section.EXAM_TIPS)

    def has_gallery_images(self, section):
        return self.gallery_images(section).exists()

    def get_publication_missing_fields(self):
        missing = []
        for field in self.REQUIRED_FIELDS:
            if field == "equation_img" and self.has_gallery_images(ReactionImage.Section.EQUATION):
                continue
            if not getattr(self, field):
                missing.append(field)
        return missing

    def missing_fields_display(self):
        missing = self.get_publication_missing_fields()
        if not missing:
            return "完整"
        return "、".join(self.REQUIRED_FIELDS[field] for field in missing)

    def content_completeness(self):
        total = len(self.REQUIRED_FIELDS)
        complete = total - len(self.get_publication_missing_fields())
        return f"{complete}/{total}"

    def clean(self):
        super().clean()
        if self.status != self.Status.PUBLISHED:
            return
        missing = self.get_publication_missing_fields()
        if missing:
            raise ValidationError({field: f"发布前请补充{self.REQUIRED_FIELDS[field]}。" for field in missing})


class NamedReaction(BaseReactionContent):
    images = GenericRelation("ReactionImage", content_type_field="content_type", object_id_field="object_id")
    category = models.ForeignKey(
        NamedReactionCategory,
        verbose_name="人名反应分类",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reactions",
    )

    class Meta:
        ordering = ["name_en", "name_zh"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["name_zh"]),
            models.Index(fields=["name_en"]),
        ]
        verbose_name = "人名反应"
        verbose_name_plural = "人名反应"

    def get_absolute_url(self):
        return reverse("reaction_detail", kwargs={"slug": self.slug})


class GeneralReaction(BaseReactionContent):
    images = GenericRelation("ReactionImage", content_type_field="content_type", object_id_field="object_id")
    category = models.ForeignKey(
        GeneralReactionCategory,
        verbose_name="常见有机反应分类",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reactions",
    )

    class Meta:
        ordering = ["name_zh", "name_en"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["name_zh"]),
            models.Index(fields=["name_en"]),
        ]
        verbose_name = "常见有机反应"
        verbose_name_plural = "常见有机反应"

    def get_absolute_url(self):
        return reverse("general_reaction_detail", kwargs={"slug": self.slug})


class ReactionImage(models.Model):
    MAX_IMAGES_PER_SECTION = 10

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REDRAW = "redraw", "需重画"

    class Section(models.TextChoices):
        EQUATION = "equation", "方程式图"
        MECHANISM = "mechanism", "机理图"
        CONDITION = "condition", "反应条件附图"
        MECHANISM_TEXT = "mechanism_text", "机理文字附图"
        EXAM_TIPS = "exam_tips", "考点附图"

    content_type = models.ForeignKey(ContentType, verbose_name="内容类型", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField("内容 ID")
    content_object = GenericForeignKey("content_type", "object_id")
    section = models.CharField("图片区域", max_length=30, choices=Section.choices)
    image = models.FileField("图片", upload_to=ReactionGalleryImageUploadTo())
    caption = models.CharField("图片说明", max_length=160, blank=True)
    review_status = models.CharField("审核状态", max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    sort_order = models.PositiveIntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["section", "sort_order", "pk"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "section"]),
            models.Index(fields=["section", "sort_order"]),
        ]
        verbose_name = "反应附图"
        verbose_name_plural = "反应附图"

    def __str__(self):
        target = self.content_object or f"{self.content_type_id}:{self.object_id}"
        return f"{target} - {self.get_section_display()}"

    def clean(self):
        super().clean()
        if not self.content_type_id or not self.object_id or not self.section:
            return
        count = (
            ReactionImage.objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
                section=self.section,
            )
            .exclude(pk=self.pk)
            .count()
        )
        if count >= self.MAX_IMAGES_PER_SECTION:
            raise ValidationError({"section": f"每个区域最多上传 {self.MAX_IMAGES_PER_SECTION} 张图片。"})

    def get_image_src(self):
        return self.image.url if self.image else ""

class SyntheticRoute(models.Model):
    Status = PublishStatus
    PUBLICATION_REQUIRED_FIELDS = {
        "target_product": "目标产物",
        "summary": "路线摘要",
        "steps": "至少一个路线步骤",
    }

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "基础"
        INTERMEDIATE = "intermediate", "中等"
        ADVANCED = "advanced", "进阶"

    target_product = models.CharField("目标产物", max_length=200)
    target_structure_image = models.FileField("目标产物结构式图片", upload_to="route_structures/", blank=True,
        help_text="上传目标产物结构式的 SVG 或 PNG 图片")
    target_structure_image_url = models.CharField("目标产物结构式图片 URL", max_length=500, blank=True,
        help_text="已有图床路径时填写，例如 /static/images/routes/route_xxx.svg")
    target_structure_image_caption = models.CharField("目标产物结构式说明", max_length=200, blank=True)
    slug = models.SlugField("URL 标识", max_length=140, unique=True)
    summary = models.TextField("路线摘要", blank=True)
    advantages = models.TextField("优点", blank=True)
    disadvantages = models.TextField("缺点", blank=True)
    difficulty = models.CharField("难度", max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    source = models.CharField("来源", max_length=200, blank=True)
    related_reactions = models.ManyToManyField(Reaction, verbose_name="相关反应", blank=True, related_name="routes")
    related_named_reactions = models.ManyToManyField(
        NamedReaction,
        verbose_name="相关人名反应",
        blank=True,
        related_name="routes",
    )
    related_general_reactions = models.ManyToManyField(
        GeneralReaction,
        verbose_name="相关常见有机反应",
        blank=True,
        related_name="routes",
    )
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = PublishedManager()
    published = PublishedOnlyManager()

    class Meta:
        ordering = ["target_product"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["target_product"]),
        ]
        verbose_name = "合成路线"
        verbose_name_plural = "合成路线"

    def __str__(self):
        return self.target_product

    def get_absolute_url(self):
        return reverse("route_detail", kwargs={"slug": self.slug})

    def get_target_structure_image_src(self):
        return first_image_source(self.target_structure_image, self.target_structure_image_url)

    def get_publication_missing_fields(self):
        missing_fields = []
        if not self.target_product.strip():
            missing_fields.append("target_product")
        if not self.summary.strip():
            missing_fields.append("summary")
        if not self.pk or not self.steps.exists():
            missing_fields.append("steps")
        return missing_fields

    def content_completeness(self):
        total = len(self.PUBLICATION_REQUIRED_FIELDS)
        complete = total - len(self.get_publication_missing_fields())
        return f"{complete}/{total}"

    def clean(self):
        super().clean()
        if self.status != self.Status.PUBLISHED:
            return
        missing_fields = self.get_publication_missing_fields()
        if missing_fields:
            raise ValidationError(
                {field: f"发布前请填写{self.PUBLICATION_REQUIRED_FIELDS[field]}。" for field in missing_fields}
            )


class RouteStep(models.Model):
    route = models.ForeignKey(SyntheticRoute, verbose_name="所属路线", on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField("步骤序号")
    title = models.CharField("步骤标题", max_length=100)
    reactant_structure_image = models.FileField("反应物结构式图片", upload_to="route_step_structures/", blank=True,
        help_text="上传反应物结构式的 SVG 或 PNG")
    reactant_structure_image_url = models.CharField("反应物结构式图片 URL", max_length=500, blank=True)
    product_structure_image = models.FileField("产物结构式图片", upload_to="route_step_structures/", blank=True,
        help_text="上传产物结构式的 SVG 或 PNG")
    product_structure_image_url = models.CharField("产物结构式图片 URL", max_length=500, blank=True)
    structure_image_caption = models.CharField("步骤结构式说明", max_length=200, blank=True)
    reagents = models.TextField("试剂", blank=True)
    condition = models.TextField("条件", blank=True)
    yield_text = models.CharField("产率", max_length=50, blank=True)
    related_reactions = models.ManyToManyField(Reaction, verbose_name="相关反应", blank=True, related_name="route_steps")
    related_named_reactions = models.ManyToManyField(
        NamedReaction,
        verbose_name="相关人名反应",
        blank=True,
        related_name="route_steps",
    )
    related_general_reactions = models.ManyToManyField(
        GeneralReaction,
        verbose_name="相关常见有机反应",
        blank=True,
        related_name="route_steps",
    )
    note = models.TextField("说明", blank=True)

    class Meta:
        ordering = ["step_number", "id"]
        unique_together = [("route", "step_number")]
        verbose_name = "路线步骤"
        verbose_name_plural = "路线步骤"

    def __str__(self):
        return f"{self.route.target_product} - Step {self.step_number}: {self.title}"

    def get_reactant_structure_image_src(self):
        return first_image_source(self.reactant_structure_image, self.reactant_structure_image_url)

    def get_product_structure_image_src(self):
        return first_image_source(self.product_structure_image, self.product_structure_image_url)


class LearningResource(models.Model):
    Status = PublishStatus

    class Category(models.TextChoices):
        PAST_EXAM = "past_exam", "真题"
        EXERCISE = "exercise", "习题"
        ANSWER = "answer", "答案"
        COURSEWARE = "courseware", "课件"
        LECTURE = "lecture", "讲义"
        SYLLABUS = "syllabus", "大纲"
        BOOK = "book", "教材/复习书"
        OTHER = "other", "其他"

    class SourceType(models.TextChoices):
        UPLOAD = "upload", "上传文件"
        EXTERNAL = "external", "外部路径"

    title = models.CharField("资料标题", max_length=255)
    category = models.CharField("分类", max_length=30, choices=Category.choices, default=Category.OTHER)
    year = models.PositiveIntegerField("年份", null=True, blank=True)
    file_type = models.CharField("文件类型", max_length=20)
    size_bytes = models.PositiveBigIntegerField("文件大小", default=0)
    local_path = models.TextField("本地路径", unique=True, help_text="如需树形展示，按 分类/年份/文件名 的目录结构组织路径")
    relative_path = models.TextField("相对路径", blank=True)
    source_folder = models.CharField("来源文件夹", max_length=120, blank=True)
    has_answer = models.BooleanField("含答案", default=False)
    source_type = models.CharField(
        "来源类型",
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.EXTERNAL,
    )
    uploaded_file = models.FileField("上传文件", upload_to="learning_resources/", blank=True)
    external_path = models.TextField("外部路径", blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = PublishedManager()
    published = PublishedOnlyManager()

    class Meta:
        ordering = ["category", "-year", "title"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["year"]),
            models.Index(fields=["file_type"]),
        ]
        verbose_name = "学习资料"
        verbose_name_plural = "学习资料"

    def __str__(self):
        return self.title

    def size_label(self):
        if self.size_bytes >= 1024 * 1024:
            return f"{self.size_bytes / 1024 / 1024:.1f} MB"
        if self.size_bytes >= 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        return f"{self.size_bytes} B"

    def clean(self):
        super().clean()
        if self.status != self.Status.PUBLISHED:
            return
        if self.uploaded_file or self.external_path.strip() or self.local_path.strip():
            return
        raise ValidationError({"external_path": "发布前请上传文件或填写外部路径。"})


class Announcement(models.Model):
    class Importance(models.TextChoices):
        LOW = "low", "普通"
        HIGH = "high", "重要"

    title = models.CharField("公告标题", max_length=200)
    content = models.TextField("公告内容")
    importance = models.CharField("重要性", max_length=10, choices=Importance.choices, default=Importance.LOW)
    is_pinned = models.BooleanField("置顶", default=False, help_text="置顶公告始终显示在顶部，且不设显示时限")
    is_active = models.BooleanField("显示", default=True)
    show_from = models.DateTimeField("开始显示", blank=True, null=True, help_text="非置顶公告：在此时间之后才显示")
    show_until = models.DateTimeField("截止显示", blank=True, null=True, help_text="非置顶公告：在此时间之后自动隐藏")
    message_sent_at = models.DateTimeField("消息推送时间", blank=True, null=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        verbose_name = "公告"
        verbose_name_plural = "公告"

    def __str__(self):
        prefix = "📌 " if self.is_pinned else ""
        return f"{prefix}{self.title}"


class Feedback(models.Model):
    class Category(models.TextChoices):
        CONTENT = "content", "内容纠错"
        FEATURE = "feature", "功能建议"
        DATA = "data", "数据补充"
        USAGE = "usage", "使用问题"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        PROCESSING = "processing", "处理中"
        RESOLVED = "resolved", "已处理"
        CLOSED = "closed", "已关闭"

    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("名称", max_length=100)
    email = models.EmailField("电子邮件", max_length=200, blank=True)
    category = models.CharField("类型", max_length=20, choices=Category.choices, default=Category.OTHER)
    content = models.TextField("反馈内容")
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    reply = models.TextField("管理员回复", blank=True, help_text="此回复将对用户可见")
    internal_note = models.TextField("内部备注", blank=True, help_text="仅管理员可见")
    handled_by = models.ForeignKey("auth.User", verbose_name="处理人", on_delete=models.SET_NULL, null=True, blank=True, related_name="handled_feedbacks")
    handled_at = models.DateTimeField("处理时间", blank=True, null=True)
    is_read = models.BooleanField("已读", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "意见反馈"
        verbose_name_plural = "意见反馈"

    def __str__(self):
        return f"{self.get_category_display()} - {self.name} - {self.content[:50]}"


class Message(models.Model):
    class Type(models.TextChoices):
        ANNOUNCEMENT = "announcement", "公告通知"
        FEEDBACK_REPLY = "feedback_reply", "反馈回复"
        FEEDBACK_STATUS = "feedback_status", "反馈状态更新"
        REVIEW_NOTICE = "review_notice", "审核通知"
        SYSTEM = "system", "系统提醒"

    recipient = models.ForeignKey("auth.User", verbose_name="接收人", on_delete=models.CASCADE)
    msg_type = models.CharField("消息类型", max_length=30, choices=Type.choices)
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    is_read = models.BooleanField("已读", default=False)
    related_url = models.CharField("相关链接", max_length=500, blank=True)
    created_at = models.DateTimeField("发送时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "站内消息"
        verbose_name_plural = "站内消息"

    def __str__(self):
        return f"[{self.get_msg_type_display()}] {self.title}"


class StudyTopic(models.Model):
    Status = PublishStatus

    name = models.CharField("专题名称", max_length=120)
    slug = models.SlugField("URL 标识", max_length=140, unique=True)
    summary = models.TextField("专题简介", blank=True)
    learning_goals = models.TextField("学习目标", blank=True)
    exam_focus = models.TextField("考试重点", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    named_reactions = models.ManyToManyField("NamedReaction", verbose_name="人名反应", blank=True, related_name="study_topics")
    general_reactions = models.ManyToManyField("GeneralReaction", verbose_name="常见有机反应", blank=True, related_name="study_topics")
    routes = models.ManyToManyField("SyntheticRoute", verbose_name="合成路线", blank=True, related_name="study_topics")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "考研专题"
        verbose_name_plural = "考研专题"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("study_topic_detail", kwargs={"slug": self.slug})


class ReactionComparison(models.Model):
    Status = PublishStatus

    title = models.CharField("对比标题", max_length=160)
    slug = models.SlugField("URL 标识", max_length=180, unique=True)
    summary = models.TextField("对比说明", blank=True)
    reaction_a_content_type = models.ForeignKey(ContentType, verbose_name="反应 A 类型", on_delete=models.PROTECT, related_name="comparison_a_set")
    reaction_a_object_id = models.PositiveIntegerField("反应 A ID")
    reaction_a = GenericForeignKey("reaction_a_content_type", "reaction_a_object_id")
    reaction_b_content_type = models.ForeignKey(ContentType, verbose_name="反应 B 类型", on_delete=models.PROTECT, related_name="comparison_b_set")
    reaction_b_object_id = models.PositiveIntegerField("反应 B ID")
    reaction_b = GenericForeignKey("reaction_b_content_type", "reaction_b_object_id")
    substrate_difference = models.TextField("适用底物差异", blank=True)
    condition_difference = models.TextField("反应条件差异", blank=True)
    product_difference = models.TextField("主要产物差异", blank=True)
    exam_patterns = models.TextField("常见考法", blank=True)
    pitfalls = models.TextField("易错点", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "易混反应对比"
        verbose_name_plural = "易混反应对比"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("reaction_comparison_detail", kwargs={"slug": self.slug})

    def clean(self):
        super().clean()
        if self.reaction_a_content_type_id and self.reaction_b_content_type_id:
            if (
                self.reaction_a_content_type_id == self.reaction_b_content_type_id
                and self.reaction_a_object_id == self.reaction_b_object_id
            ):
                raise ValidationError("反应 A 和反应 B 必须是两个不同的反应。")


class VisitCounter(models.Model):
    SITE_KEY = "site"

    key = models.CharField("统计键", max_length=160, unique=True)
    label = models.CharField("统计名称", max_length=160, blank=True)
    total_count = models.PositiveIntegerField("总访问量", default=0)
    today_count = models.PositiveIntegerField("今日访问量", default=0)
    today_date = models.DateField("今日日期", null=True, blank=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "访问统计"
        verbose_name_plural = "访问统计"

    def __str__(self):
        return self.label or self.key

    @classmethod
    def key_for_object(cls, obj):
        return f"{obj._meta.label_lower}:{obj.pk}"


class OpLog(models.Model):
    """Admin action audit log."""
    user = models.ForeignKey("auth.User", verbose_name="操作人", on_delete=models.SET_NULL, null=True)
    action = models.CharField("操作", max_length=50)
    model_name = models.CharField("模型", max_length=50)
    object_repr = models.CharField("对象", max_length=200, blank=True)
    detail = models.TextField("详情", blank=True)
    ip = models.GenericIPAddressField("IP", blank=True, null=True)
    created_at = models.DateTimeField("操作时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"

    def __str__(self):
        return f"{self.user} {self.action} {self.object_repr}"


class CommonReaction(models.Model):
    """Non-person reactions — common/classic reactions like substitution, addition, elimination."""
    Status = PublishStatus

    name_zh = models.CharField("反应名称", max_length=100)
    slug = models.SlugField("URL 标识", max_length=120, unique=True)
    content = models.TextField("内容说明", blank=True, help_text="反应机理、要点说明等")
    equation_img = models.FileField("反应方程式图片", upload_to="common_reactions/", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["sort_order", "name_zh"]
        verbose_name = "常见反应（非人名）"
        verbose_name_plural = "常见反应（非人名）"

    def __str__(self):
        return self.name_zh


class Favorite(models.Model):
    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, verbose_name="内容类型", on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField("内容 ID", null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    route = models.ForeignKey(SyntheticRoute, verbose_name="路线", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = "收藏"
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="unique_fav_content"),
            models.UniqueConstraint(fields=["user", "route"], name="unique_fav_route"),
        ]

    def __str__(self):
        if self.content_object:
            return f"{self.user.username} 收藏: {self.content_object}"
        if self.route:
            return f"{self.user.username} 收藏路线: {self.route.target_product}"
        return str(self.pk)


class StudyNote(models.Model):
    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, verbose_name="内容类型", on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField("内容 ID", null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    route = models.ForeignKey(SyntheticRoute, verbose_name="路线", on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField("笔记内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学习笔记"
        verbose_name_plural = "学习笔记"

    def __str__(self):
        target = self.content_object or self.route
        return f"{self.user.username} 的笔记 - {target}"


class StudyProgress(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待学习"
        LEARNED = "learned", "已学"
        REVIEW = "review", "待复习"

    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, verbose_name="内容类型", on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField("内容 ID", null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    route = models.ForeignKey(SyntheticRoute, verbose_name="路线", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学习进度"
        verbose_name_plural = "学习进度"
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="unique_progress_content"),
            models.UniqueConstraint(fields=["user", "route"], name="unique_progress_route"),
        ]

    def __str__(self):
        target = self.content_object or self.route
        return f"{self.user.username} - {target} - {self.get_status_display()}"

