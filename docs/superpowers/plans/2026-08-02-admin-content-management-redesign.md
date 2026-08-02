# 后台内容管理重构实施计划

> **给执行代理的要求：** 实施本计划时必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项执行。每个任务都包含独立测试、实现和提交步骤。

**目标：** 将 OrganicChemHub 后台重构为“Django Admin 日常编辑 + 专用后台工具页复杂流程”的内容管理系统。

**架构：** 先新增清晰的新内容模型和测试，再逐步替换 Admin、前台查询和运营工具页。旧数据不迁移，旧模型可在过渡期保留，但前台和后台主路径最终使用 `NamedReaction`、`GeneralReaction`、`NamedReactionCategory`、`GeneralReactionCategory`。

**技术栈：** Python 3.11、Django 5.2、SQLite、Django Admin、Django Templates、Bootstrap、Django TestCase。

## 全局约束

- 后台主编辑界面继续使用 Django Admin。
- 复杂工作流拆成专用后台工具页。
- 人名反应和常见有机反应使用两套独立模型。
- 人名反应分类和常见有机反应分类使用两套独立模型。
- 本版本不围绕 SMILES 设计核心流程。
- 不要求迁移旧数据。
- 尽量保留当前前台 UI 风格。
- 机理图可选，不计入发布完整度。
- 学习资料保留轻量可用能力。

---

## 文件结构

- 修改：`reactions/models.py`，新增核心模型、图片命名、完整度和发布校验。
- 修改：`reactions/admin.py`，重组 Django Admin 注册、列表、筛选、批量操作和工具入口。
- 修改：`reactions/admin_helpers.py`，统一图片预览、缩略图和 CSV 辅助函数。
- 新建：`reactions/admin_forms.py`，放置 CSV 导入、消息群发、图片维护和资料登记表单。
- 新建：`reactions/admin_tools.py`，放置专用后台工具页视图。
- 修改：`reactions/urls.py`，新增常见有机反应前台路由。
- 修改：`reactions/views/home.py`，首页改读新模型。
- 修改：`reactions/views/reactions.py`，人名反应和常见有机反应列表/详情适配。
- 修改：`reactions/views/routes.py`，合成路线关联两套反应模型。
- 修改：`reactions/views/feedback.py`，学习资料双轨字段适配。
- 修改：`templates/reactions/home.html`，首页入口和精选内容适配新模型。
- 修改：`templates/reactions/reaction_list.html`，保留 UI，适配人名反应。
- 修改：`templates/reactions/reaction_detail.html`，保留 UI，适配新图片和字段。
- 新建：`templates/reactions/general_reaction_list.html`，常见有机反应列表页。
- 新建：`templates/reactions/general_reaction_detail.html`，常见有机反应详情页。
- 新建：`templates/admin/reactions/dashboard.html`，内容质量仪表盘。
- 新建：`templates/admin/reactions/import.html`，CSV 导入工具页。
- 新建：`templates/admin/reactions/images.html`，图片维护工具页。
- 新建：`templates/admin/operations/message_send.html`，消息群发工具页。
- 新建：`templates/admin/operations/message_cleanup.html`，消息清理工具页。
- 新建：`templates/admin/resources/import_or_upload.html`，学习资料上传/登记工具页。
- 修改：`reactions/tests.py`，覆盖模型、Admin、工具页和前台兼容。
- 新建：`reactions/migrations/0014_admin_content_redesign.py`，新 schema 迁移。
- 修改：`README.md`，记录新版后台管理入口和验证命令。
- 修改：`docs/CHANGELOG.md`，记录版本变更。

---

## 任务 1：新增核心模型和发布规则

**文件：**

- 修改：`reactions/models.py`
- 新建：`reactions/migrations/0014_admin_content_redesign.py`
- 修改：`reactions/tests.py`

**接口：**

- 产出：`NamedReactionCategory`
- 产出：`GeneralReactionCategory`
- 产出：`NamedReaction`
- 产出：`GeneralReaction`
- 产出：`get_publication_missing_fields() -> list[str]`
- 产出：`content_completeness() -> str`
- 产出：`missing_fields_display() -> str`

### 步骤

- [ ] **步骤 1：写失败测试**

在 `reactions/tests.py` 顶部导入新模型名：

```python
from reactions.models import (
    GeneralReaction,
    GeneralReactionCategory,
    NamedReaction,
    NamedReactionCategory,
    PublishStatus,
)
```

如果该文件已有 `from reactions.models import ...`，把这些名字合并进去，不新增第二段重复导入。

在 `reactions/tests.py` 末尾追加：

```python
class AdminRedesignModelTests(TestCase):
    def test_named_reaction_requires_core_fields_and_images_for_publish(self):
        reaction = NamedReaction(
            name_zh="维蒂希反应",
            name_en="Wittig Reaction",
            slug="wittig-reaction",
            status=PublishStatus.PUBLISHED,
        )

        with self.assertRaises(ValidationError) as context:
            reaction.full_clean()

        self.assertIn("summary", context.exception.message_dict)
        self.assertIn("condition", context.exception.message_dict)
        self.assertIn("exam_tips", context.exception.message_dict)
        self.assertIn("reference", context.exception.message_dict)
        self.assertIn("equation_img", context.exception.message_dict)
        self.assertIn("thumbnail_img", context.exception.message_dict)
        self.assertNotIn("mechanism_img", context.exception.message_dict)

    def test_general_reaction_has_separate_category_and_optional_mechanism_image(self):
        category = GeneralReactionCategory.objects.create(name="加成反应", slug="addition")
        reaction = GeneralReaction(
            name_zh="亲电加成",
            name_en="Electrophilic Addition",
            slug="electrophilic-addition",
            category=category,
            summary="烯烃与亲电试剂加成。",
            condition="酸性或卤素条件。",
            exam_tips="注意马氏规则。",
            reference="教材。",
            equation_img="general_reactions/general_electrophilic_addition_equation.svg",
            thumbnail_img="general_reactions/general_electrophilic_addition_thumbnail.svg",
            status=PublishStatus.PUBLISHED,
        )

        reaction.full_clean()
        self.assertEqual(reaction.get_publication_missing_fields(), [])
        self.assertEqual(reaction.content_completeness(), "6/6")
        self.assertEqual(reaction.missing_fields_display(), "完整")
```

- [ ] **步骤 2：运行测试确认失败**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminRedesignModelTests
```

期望：失败，错误原因是新模型尚未定义或无法导入。

- [ ] **步骤 3：实现分类模型**

在 `reactions/models.py` 中保留现有旧模型，并在 `ReactionType` 附近新增：

```python
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
```

- [ ] **步骤 4：实现共享反应基类**

在 `reactions/models.py` 中新增抽象基类：

```python
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

    def get_publication_missing_fields(self):
        return [field for field in self.REQUIRED_FIELDS if not getattr(self, field)]

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
```

- [ ] **步骤 5：实现两套反应模型**

在 `BaseReactionContent` 后新增：

```python
class NamedReaction(BaseReactionContent):
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
```

- [ ] **步骤 6：更新路线和资料模型**

在 `SyntheticRoute` 新增：

```python
related_named_reactions = models.ManyToManyField(NamedReaction, verbose_name="相关人名反应", blank=True, related_name="routes")
related_general_reactions = models.ManyToManyField(GeneralReaction, verbose_name="相关常见有机反应", blank=True, related_name="routes")
```

在 `RouteStep` 新增：

```python
related_named_reactions = models.ManyToManyField(NamedReaction, verbose_name="相关人名反应", blank=True, related_name="route_steps")
related_general_reactions = models.ManyToManyField(GeneralReaction, verbose_name="相关常见有机反应", blank=True, related_name="route_steps")
```

在 `LearningResource` 新增来源类型、上传文件和外部路径字段，并实现发布校验。保留旧路径字段，降低对现有页面的冲击。

```python
class SourceType(models.TextChoices):
    UPLOAD = "upload", "上传文件"
    EXTERNAL = "external", "外部路径"

source_type = models.CharField("来源类型", max_length=20, choices=SourceType.choices, default=SourceType.EXTERNAL)
uploaded_file = models.FileField("上传文件", upload_to="learning_resources/", blank=True)
external_path = models.TextField("外部路径", blank=True)
```

`LearningResource.clean()` 规则：当 `status == PublishStatus.PUBLISHED` 且没有 `uploaded_file`、`external_path`、`local_path` 任意一种来源时，抛出 `ValidationError`。

- [ ] **步骤 7：生成并应用迁移**

运行：

```powershell
.\.venv\Scripts\python manage.py makemigrations reactions --name admin_content_redesign
.\.venv\Scripts\python manage.py migrate
```

期望：生成并应用新迁移，不要求旧数据迁移。

- [ ] **步骤 8：运行模型测试**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminRedesignModelTests
```

期望：通过。

- [ ] **步骤 9：提交**

运行：

```powershell
git add reactions/models.py reactions/migrations reactions/tests.py
git commit -m "feat: add redesigned content models"
```

---

## 任务 2：实现 Django Admin 标准内容管理层

**文件：**

- 修改：`reactions/admin_helpers.py`
- 修改：`reactions/admin.py`
- 修改：`reactions/tests.py`

**接口：**

- 消费：任务 1 的新模型。
- 产出：`ReactionAdminMixin`。
- 产出：人名反应、常见有机反应、两套分类的 Admin 注册。
- 产出：批量发布、批量归档和 CSV 导出动作。

### 步骤

- [ ] **步骤 1：写失败测试**

在 `reactions/tests.py` 追加：

```python
class AdminRedesignRegistrationTests(TestCase):
    def test_new_content_models_are_registered(self):
        self.assertIn(NamedReaction, admin.site._registry)
        self.assertIn(GeneralReaction, admin.site._registry)
        self.assertIn(NamedReactionCategory, admin.site._registry)
        self.assertIn(GeneralReactionCategory, admin.site._registry)

    def test_mechanism_image_not_required_for_admin_publish(self):
        category = NamedReactionCategory.objects.create(name="重排反应", slug="rearrangement")
        reaction = NamedReaction.objects.create(
            name_zh="测试反应",
            name_en="Test Reaction",
            slug="test-reaction-admin",
            category=category,
            summary="摘要",
            condition="条件",
            exam_tips="考点",
            reference="来源",
            equation_img="named_reactions/reaction_test_reaction_admin_equation.svg",
            thumbnail_img="named_reactions/reaction_test_reaction_admin_thumbnail.svg",
        )
        model_admin = admin.site._registry[NamedReaction]
        request = RequestFactory().post("/admin/")
        request._messages = CookieStorage(request)

        model_admin.publish_selected(request, NamedReaction.objects.filter(pk=reaction.pk))

        reaction.refresh_from_db()
        self.assertEqual(reaction.status, PublishStatus.PUBLISHED)
```

- [ ] **步骤 2：运行测试确认失败**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminRedesignRegistrationTests
```

期望：失败，因为新模型尚未注册到 Admin。

- [ ] **步骤 3：扩展 Admin 辅助函数**

在 `reactions/admin_helpers.py` 中确保存在：

```python
def image_preview(url, max_w=420, max_h=220):
    if not url:
        return "暂无图片"
    return format_html(
        '<img src="{}" style="max-width:{}px;max-height:{}px;background:#fff;border:1px solid #d8dee8;border-radius:8px;padding:8px;">',
        url,
        max_w,
        max_h,
    )


def thumbnail_img(url):
    if not url:
        return "—"
    return format_html(
        '<img src="{}" style="width:60px;height:60px;object-fit:contain;background:#fff;border:1px solid #ddd;border-radius:4px;">',
        url,
    )
```

- [ ] **步骤 4：实现共享 ReactionAdminMixin**

在 `reactions/admin.py` 中新增共享 Admin mixin，包含：

- `list_display`: 中文名、英文名、分类、缩略图、状态、完整度、缺失字段、更新时间。
- `list_filter`: 状态、分类、标签、官能团、创建时间、更新时间。
- `search_fields`: 中文名、英文名、别名。
- `filter_horizontal`: 标签、官能团。
- 图片预览只读字段。
- `publish_selected`、`archive_selected`、`export_selected_as_csv`。

- [ ] **步骤 5：注册新 Admin 类**

在 `reactions/admin.py` 中注册：

```python
@admin.register(NamedReaction)
class NamedReactionAdmin(ReactionAdminMixin, admin.ModelAdmin):
    pass


@admin.register(GeneralReaction)
class GeneralReactionAdmin(ReactionAdminMixin, admin.ModelAdmin):
    pass
```

同时注册 `NamedReactionCategoryAdmin` 和 `GeneralReactionCategoryAdmin`，列表列为 `name`、`slug`、`sort_order`、`is_active`。

- [ ] **步骤 6：更新合成路线 Admin**

给 `SyntheticRouteAdmin` 和 `RouteStepAdmin` 增加 `related_named_reactions`、`related_general_reactions` 的筛选、横向选择和 CSV 导出字段。

- [ ] **步骤 7：运行 Admin 测试**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminRedesignRegistrationTests
```

期望：通过。

- [ ] **步骤 8：提交**

运行：

```powershell
git add reactions/admin.py reactions/admin_helpers.py reactions/tests.py
git commit -m "feat: add redesigned admin content management"
```

---

## 任务 3：搭建专用后台工具页框架

**文件：**

- 新建：`reactions/admin_forms.py`
- 新建：`reactions/admin_tools.py`
- 修改：`reactions/admin.py`
- 新建：`templates/admin/reactions/dashboard.html`
- 新建：`templates/admin/reactions/import.html`
- 新建：`templates/admin/reactions/images.html`
- 新建：`templates/admin/operations/message_send.html`
- 新建：`templates/admin/operations/message_cleanup.html`
- 新建：`templates/admin/resources/import_or_upload.html`
- 修改：`reactions/tests.py`

**接口：**

- 产出：`dashboard_view(request)`。
- 产出：`reaction_import_view(request)`。
- 产出：`image_maintenance_view(request)`。
- 产出：`message_broadcast_view(request)`。
- 产出：`message_cleanup_view(request)`。
- 产出：`resource_upload_or_register_view(request)`。

### 步骤

- [ ] **步骤 1：写失败测试**

在 `reactions/tests.py` 追加：

```python
class AdminToolPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(self.user)

    def test_dashboard_loads(self):
        response = self.client.get("/admin/reactions/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "内容质量仪表盘")

    def test_import_page_loads(self):
        response = self.client.get("/admin/reactions/import/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CSV 导入")

    def test_image_page_loads(self):
        response = self.client.get("/admin/reactions/images/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "图片维护")

    def test_message_broadcast_page_loads(self):
        response = self.client.get("/admin/operations/messages/send/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "站内消息群发")

    def test_message_cleanup_page_loads(self):
        response = self.client.get("/admin/operations/messages/cleanup/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "消息清理")

    def test_resource_tool_page_loads(self):
        response = self.client.get("/admin/resources/import-or-upload/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "学习资料上传和登记")
```

- [ ] **步骤 2：运行测试确认失败**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminToolPageTests
```

期望：失败，页面返回 404。

- [ ] **步骤 3：新增后台工具表单**

创建 `reactions/admin_forms.py`：

```python
from django import forms

from .models import Message


class ReactionCsvImportForm(forms.Form):
    target = forms.ChoiceField(label="导入目标", choices=(("named", "人名反应"), ("general", "常见有机反应")))
    mode = forms.ChoiceField(label="导入模式", choices=(("create", "仅新增"), ("upsert", "新增并更新")))
    csv_file = forms.FileField(label="CSV 文件")


class MessageBroadcastForm(forms.Form):
    target = forms.ChoiceField(label="接收范围", choices=(("all", "全部用户"), ("selected", "选中用户")))
    msg_type = forms.ChoiceField(label="消息类型", choices=Message.Type.choices)
    title = forms.CharField(label="标题", max_length=200)
    content = forms.CharField(label="内容", widget=forms.Textarea)


class MessageCleanupForm(forms.Form):
    older_than = forms.ChoiceField(label="清理范围", choices=(("3", "3 个月前"), ("6", "6 个月前"), ("12", "1 年前")))
    read_only = forms.BooleanField(label="只清理已读消息", initial=True, required=False)
    confirm = forms.BooleanField(label="确认删除", required=False)
```

- [ ] **步骤 4：新增后台工具视图**

创建 `reactions/admin_tools.py`，每个视图都返回 `TemplateResponse`，上下文包含 `admin.site.each_context(request)` 和页面标题。

- [ ] **步骤 5：挂载 Admin 工具 URL**

在 `reactions/admin.py` 中把六个工具页插入 `admin.site.get_urls()` 之前，使用 `admin.site.admin_view(...)` 包裹。

- [ ] **步骤 6：创建最小模板**

每个模板继承 `admin/base_site.html`，用中文标题展示页面名称，并渲染表单或统计区块。

- [ ] **步骤 7：运行测试**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminToolPageTests
```

期望：通过。

- [ ] **步骤 8：提交**

运行：

```powershell
git add reactions/admin_forms.py reactions/admin_tools.py reactions/admin.py templates/admin reactions/tests.py
git commit -m "feat: add admin tool page framework"
```

---

## 任务 4：实现 CSV 导入、仪表盘和图片维护逻辑

**文件：**

- 修改：`reactions/admin_tools.py`
- 修改：`templates/admin/reactions/dashboard.html`
- 修改：`templates/admin/reactions/import.html`
- 修改：`templates/admin/reactions/images.html`
- 修改：`reactions/tests.py`

**接口：**

- 消费：`ReactionCsvImportForm`。
- 产出：导入结果 `created`、`updated`、`skipped`、`errors`。
- 产出：仪表盘统计上下文。

### 步骤

- [ ] **步骤 1：写失败行为测试**

新增测试：向 `/admin/reactions/import/` 提交一份 CSV，断言创建一条 `NamedReaction`；创建缺图反应后访问仪表盘，断言页面展示缺方程式图和缺缩略图数量。

- [ ] **步骤 2：实现 CSV 解析**

在 `admin_tools.py` 使用 `csv.DictReader` 读取 UTF-8-sig 内容。必需字段：

```python
REQUIRED_IMPORT_COLUMNS = ["name_zh", "name_en", "slug", "summary", "condition", "exam_tips", "reference", "status"]
```

- [ ] **步骤 3：实现新增和更新模式**

按中文名加英文名匹配已有记录。`create` 模式跳过已有记录；`upsert` 模式更新已有记录。

- [ ] **步骤 4：实现仪表盘统计**

统计人名反应和常见有机反应的总数、状态数、缺方程式图、缺缩略图、分类分布，以及合成路线总数和缺步骤路线数量。

- [ ] **步骤 5：实现图片维护列表**

展示缺必要图片的人名反应和常见有机反应；机理图作为可选补充项单独展示，不计入强制缺图。

- [ ] **步骤 6：运行测试**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminToolPageTests
```

期望：通过。

- [ ] **步骤 7：提交**

运行：

```powershell
git add reactions/admin_tools.py templates/admin/reactions reactions/tests.py
git commit -m "feat: implement admin import dashboard and image tools"
```

---

## 任务 5：前台适配新反应模型

**文件：**

- 修改：`reactions/views/home.py`
- 修改：`reactions/views/reactions.py`
- 修改：`reactions/urls.py`
- 修改：`templates/reactions/home.html`
- 修改：`templates/reactions/reaction_list.html`
- 修改：`templates/reactions/reaction_detail.html`
- 新建：`templates/reactions/general_reaction_list.html`
- 新建：`templates/reactions/general_reaction_detail.html`
- 修改：`reactions/tests.py`

**接口：**

- 消费：`NamedReaction.published`。
- 消费：`GeneralReaction.published`。
- 产出：`GeneralReactionListView`。
- 产出：`GeneralReactionDetailView`。

### 步骤

- [ ] **步骤 1：写失败前台测试**

新增测试：`reaction_list` 展示已发布 `NamedReaction`；`general_reaction_list` 展示已发布 `GeneralReaction`；草稿和归档内容不展示。

- [ ] **步骤 2：更新人名反应视图**

把现有 `ReactionListView` 和 `ReactionDetailView` 的数据源改为 `NamedReaction`，并把 `reaction_type` 相关显示改为 `category`。

- [ ] **步骤 3：新增常见有机反应视图和 URL**

新增 `GeneralReactionListView`、`GeneralReactionDetailView`，并在 `reactions/urls.py` 增加：

```python
path("reactions/general/", GeneralReactionListView.as_view(), name="general_reaction_list"),
path("reactions/general/<slug:slug>/", GeneralReactionDetailView.as_view(), name="general_reaction_detail"),
```

- [ ] **步骤 4：更新模板**

保留当前视觉类名和布局。使用 `reaction.category`、`get_equation_img_src`、`get_thumbnail_img_src`、`get_mechanism_img_src`。缺少机理图时不渲染机理图片区块。

- [ ] **步骤 5：运行前台测试**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.FrontendRedesignTests
```

期望：通过。

- [ ] **步骤 6：提交**

运行：

```powershell
git add reactions/views reactions/urls.py templates/reactions reactions/tests.py
git commit -m "feat: adapt frontend to redesigned reaction models"
```

---

## 任务 6：消息、反馈、公告和权限角色

**文件：**

- 修改：`reactions/models.py`
- 修改：`reactions/admin.py`
- 修改：`reactions/admin_tools.py`
- 新建：`reactions/management/commands/setup_admin_roles.py`
- 修改：`reactions/tests.py`

**接口：**

- 产出：`Announcement.message_sent_at`。
- 产出：管理命令 `setup_admin_roles`。
- 产出：消息群发和消息清理行为。

### 步骤

- [ ] **步骤 1：写失败运营测试**

新增测试：保存启用公告后为每个用户创建一条消息；重复保存同一公告不重复创建；运行 `setup_admin_roles` 后存在 `内容编辑员` 和 `运营员` 两个用户组。

- [ ] **步骤 2：实现公告推送防重复**

给 `Announcement` 新增：

```python
message_sent_at = models.DateTimeField("消息推送时间", blank=True, null=True)
```

在 `AnnouncementAdmin.save_model()` 中只在 `is_active=True` 且 `message_sent_at` 为空时创建消息，创建后写入当前时间。

- [ ] **步骤 3：实现角色初始化命令**

创建 `reactions/management/commands/setup_admin_roles.py`，按规格给 `内容编辑员` 和 `运营员` 分配模型权限。

- [ ] **步骤 4：实现消息工具逻辑**

完成消息群发和消息清理行为，包括预览数量、二次确认、创建/删除消息和写入 `OpLog`。

- [ ] **步骤 5：运行测试**

运行：

```powershell
.\.venv\Scripts\python manage.py test reactions.tests.AdminToolPageTests
```

期望：通过。

- [ ] **步骤 6：提交**

运行：

```powershell
git add reactions/models.py reactions/admin.py reactions/admin_tools.py reactions/management/commands reactions/migrations reactions/tests.py
git commit -m "feat: add operations messaging and admin roles"
```

---

## 任务 7：最终验证和文档更新

**文件：**

- 修改：`README.md`
- 修改：`docs/CHANGELOG.md`

**接口：**

- 消费：前面所有任务。
- 产出：已记录的后台重构说明。

### 步骤

- [ ] **步骤 1：更新文档**

在 README 和 CHANGELOG 中新增中文说明：

```markdown
## 后台内容管理重构

- 人名反应和常见有机反应拆成两套内容库。
- 反应方程式图和缩略图是发布质量检查重点，机理图可选。
- 专用后台工具页包括内容质量仪表盘、CSV 导入、图片维护、消息群发、资料上传/登记和消息清理。
- 可运行 `python manage.py setup_admin_roles` 初始化内容编辑员和运营员角色。
```

- [ ] **步骤 2：运行完整验证**

运行：

```powershell
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py test
```

期望：两个命令都通过。

- [ ] **步骤 3：检查迁移状态**

运行：

```powershell
.\.venv\Scripts\python manage.py showmigrations reactions
```

期望：新迁移存在并已应用。

- [ ] **步骤 4：提交**

运行：

```powershell
git add README.md docs/CHANGELOG.md
git commit -m "docs: document admin content redesign"
```

---

## 自查

规格覆盖：

- 两套独立反应模型：任务 1。
- 两套独立分类模型：任务 1 和任务 2。
- Django Admin 日常编辑：任务 2。
- 专用后台工具页：任务 3 和任务 4。
- 机理图可选：任务 1 和任务 5。
- 学习资料作为次要双轨模块：任务 1 和任务 3。
- 公告、反馈、站内消息、权限：任务 6。
- 前台 UI 兼容：任务 5。
- 测试和最终验证：全部任务，尤其任务 7。

占位检查：

- 本计划不保留 TBD、TODO 或未定义的占位任务。

风险说明：

- 旧模型可以在过渡期保留，以降低一次性重构风险。到任务 5 结束时，前台和后台主路径应切换到新模型。
- 因规格明确不要求迁移旧数据，任务 5 后可能需要更新旧 fixture 和部分旧测试。
