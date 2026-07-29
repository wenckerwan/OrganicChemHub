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

    title = models.CharField("资料标题", max_length=255)
    category = models.CharField("分类", max_length=30, choices=Category.choices, default=Category.OTHER)
    year = models.PositiveIntegerField("年份", null=True, blank=True)
    file_type = models.CharField("文件类型", max_length=20)
    size_bytes = models.PositiveBigIntegerField("文件大小", default=0)
    local_path = models.TextField("本地路径", unique=True)
    relative_path = models.TextField("相对路径", blank=True)
    source_folder = models.CharField("来源文件夹", max_length=120, blank=True)
    has_answer = models.BooleanField("含答案", default=False)
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


class Favorite(models.Model):
    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.CASCADE)
    reaction = models.ForeignKey(Reaction, verbose_name="反应", on_delete=models.CASCADE, null=True, blank=True)
    route = models.ForeignKey(SyntheticRoute, verbose_name="路线", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = "收藏"
        constraints = [
            models.UniqueConstraint(fields=["user", "reaction"], name="unique_fav_reaction"),
            models.UniqueConstraint(fields=["user", "route"], name="unique_fav_route"),
        ]

    def __str__(self):
        if self.reaction:
            return f"{self.user.username} 收藏反应: {self.reaction.name_zh}"
        if self.route:
            return f"{self.user.username} 收藏路线: {self.route.target_product}"
        return str(self.pk)


class StudyNote(models.Model):
    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.CASCADE)
    reaction = models.ForeignKey(Reaction, verbose_name="反应", on_delete=models.CASCADE, null=True, blank=True)
    route = models.ForeignKey(SyntheticRoute, verbose_name="路线", on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField("笔记内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学习笔记"
        verbose_name_plural = "学习笔记"

    def __str__(self):
        target = self.reaction or self.route
        return f"{self.user.username} 的笔记 - {target}"


class StudyProgress(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待学习"
        LEARNED = "learned", "已学"
        REVIEW = "review", "待复习"

    user = models.ForeignKey("auth.User", verbose_name="用户", on_delete=models.CASCADE)
    reaction = models.ForeignKey(Reaction, verbose_name="反应", on_delete=models.CASCADE, null=True, blank=True)
    route = models.ForeignKey(SyntheticRoute, verbose_name="路线", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学习进度"
        verbose_name_plural = "学习进度"
        constraints = [
            models.UniqueConstraint(fields=["user", "reaction"], name="unique_progress_reaction"),
            models.UniqueConstraint(fields=["user", "route"], name="unique_progress_route"),
        ]

    def __str__(self):
        target = self.reaction or self.route
        return f"{self.user.username} - {target} - {self.get_status_display()}"
