from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FunctionalGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_zh", models.CharField(max_length=50, unique=True, verbose_name="中文名")),
                ("name_en", models.CharField(blank=True, max_length=80, verbose_name="英文名")),
                ("smarts", models.CharField(blank=True, max_length=200, verbose_name="SMARTS")),
                ("description", models.TextField(blank=True, verbose_name="说明")),
            ],
            options={
                "verbose_name": "官能团",
                "verbose_name_plural": "官能团",
                "ordering": ["name_zh"],
            },
        ),
        migrations.CreateModel(
            name="ReactionType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True, verbose_name="类型名称")),
                ("slug", models.SlugField(max_length=80, unique=True, verbose_name="URL 标识")),
                ("description", models.TextField(blank=True, verbose_name="类型描述")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="排序")),
            ],
            options={
                "verbose_name": "反应类型",
                "verbose_name_plural": "反应类型",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True, verbose_name="标签名称")),
                ("slug", models.SlugField(max_length=80, unique=True, verbose_name="URL 标识")),
                ("description", models.TextField(blank=True, verbose_name="标签描述")),
            ],
            options={
                "verbose_name": "标签",
                "verbose_name_plural": "标签",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Reaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_zh", models.CharField(max_length=100, verbose_name="中文名称")),
                ("name_en", models.CharField(max_length=100, verbose_name="英文名称")),
                ("slug", models.SlugField(max_length=120, unique=True, verbose_name="URL 标识")),
                ("aliases", models.CharField(blank=True, max_length=300, verbose_name="别名")),
                ("equation_smiles", models.TextField(blank=True, help_text="建议格式：反应物>>生成物", verbose_name="反应 SMILES")),
                ("summary", models.TextField(blank=True, verbose_name="简要说明")),
                ("condition", models.TextField(blank=True, verbose_name="反应条件")),
                ("mechanism", models.TextField(blank=True, verbose_name="机理说明")),
                ("scope", models.TextField(blank=True, verbose_name="适用范围")),
                ("limitations", models.TextField(blank=True, verbose_name="限制与注意事项")),
                ("exam_tips", models.TextField(blank=True, verbose_name="考点与易错点")),
                ("reference", models.TextField(blank=True, verbose_name="参考来源")),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "草稿"), ("published", "已发布"), ("archived", "已归档")],
                        default="draft",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "functional_groups",
                    models.ManyToManyField(blank=True, related_name="reactions", to="reactions.functionalgroup", verbose_name="相关官能团"),
                ),
                (
                    "reaction_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reactions",
                        to="reactions.reactiontype",
                        verbose_name="反应类型",
                    ),
                ),
                ("tags", models.ManyToManyField(blank=True, related_name="reactions", to="reactions.tag", verbose_name="标签")),
            ],
            options={
                "verbose_name": "人名反应",
                "verbose_name_plural": "人名反应",
                "ordering": ["name_en", "name_zh"],
            },
        ),
        migrations.CreateModel(
            name="SyntheticRoute",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_product", models.CharField(max_length=200, verbose_name="目标产物")),
                ("target_smiles", models.CharField(blank=True, max_length=300, verbose_name="目标产物 SMILES")),
                ("slug", models.SlugField(max_length=140, unique=True, verbose_name="URL 标识")),
                ("summary", models.TextField(blank=True, verbose_name="路线摘要")),
                ("advantages", models.TextField(blank=True, verbose_name="优点")),
                ("disadvantages", models.TextField(blank=True, verbose_name="缺点")),
                (
                    "difficulty",
                    models.CharField(
                        choices=[("beginner", "基础"), ("intermediate", "中等"), ("advanced", "进阶")],
                        default="beginner",
                        max_length=20,
                        verbose_name="难度",
                    ),
                ),
                ("source", models.CharField(blank=True, max_length=200, verbose_name="来源")),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "草稿"), ("published", "已发布"), ("archived", "已归档")],
                        default="draft",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "related_reactions",
                    models.ManyToManyField(blank=True, related_name="routes", to="reactions.reaction", verbose_name="相关反应"),
                ),
            ],
            options={
                "verbose_name": "合成路线",
                "verbose_name_plural": "合成路线",
                "ordering": ["target_product"],
            },
        ),
        migrations.CreateModel(
            name="RouteStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("step_number", models.PositiveIntegerField(verbose_name="步骤序号")),
                ("title", models.CharField(max_length=100, verbose_name="步骤标题")),
                ("reactant_smiles", models.TextField(blank=True, verbose_name="反应物 SMILES")),
                ("product_smiles", models.TextField(blank=True, verbose_name="产物 SMILES")),
                ("reagents", models.TextField(blank=True, verbose_name="试剂")),
                ("condition", models.TextField(blank=True, verbose_name="条件")),
                ("yield_text", models.CharField(blank=True, max_length=50, verbose_name="产率")),
                ("note", models.TextField(blank=True, verbose_name="说明")),
                (
                    "related_reactions",
                    models.ManyToManyField(blank=True, related_name="route_steps", to="reactions.reaction", verbose_name="相关反应"),
                ),
                (
                    "route",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="reactions.syntheticroute",
                        verbose_name="所属路线",
                    ),
                ),
            ],
            options={
                "verbose_name": "路线步骤",
                "verbose_name_plural": "路线步骤",
                "ordering": ["step_number", "id"],
                "unique_together": {("route", "step_number")},
            },
        ),
        migrations.AddIndex(
            model_name="reaction",
            index=models.Index(fields=["slug"], name="reactions_r_slug_575330_idx"),
        ),
        migrations.AddIndex(
            model_name="reaction",
            index=models.Index(fields=["status"], name="reactions_r_status_a5d650_idx"),
        ),
        migrations.AddIndex(
            model_name="reaction",
            index=models.Index(fields=["name_zh"], name="reactions_r_name_zh_483823_idx"),
        ),
        migrations.AddIndex(
            model_name="reaction",
            index=models.Index(fields=["name_en"], name="reactions_r_name_en_2abc81_idx"),
        ),
        migrations.AddIndex(
            model_name="syntheticroute",
            index=models.Index(fields=["slug"], name="reactions_s_slug_f7001a_idx"),
        ),
        migrations.AddIndex(
            model_name="syntheticroute",
            index=models.Index(fields=["status"], name="reactions_s_status_438f69_idx"),
        ),
        migrations.AddIndex(
            model_name="syntheticroute",
            index=models.Index(fields=["target_product"], name="reactions_s_target__43bc0e_idx"),
        ),
    ]
