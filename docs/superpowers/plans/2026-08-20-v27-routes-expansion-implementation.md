# v2.7 合成路线扩充实施计划

> **For agentic workers:** 本计划按测试先行执行；每个任务完成后运行对应测试，再进入下一任务。

**目标：** 让合成路线成为可训练的复习模块：按目标官能团筛选、关键步骤标记、后台维护增强。

**架构：** 两处模型变更（`RouteStep.is_key_step`、`SyntheticRoute.related_functional_groups`），一个迁移；前台列表/详情增强；Admin inline 增强。

**技术栈：** Django 5.2、Django Templates、Bootstrap 5、现有 `site.css`、Django TestCase。

## 全局约束

- 只改 `RouteStep` 和 `SyntheticRoute` 两个模型；不碰 v2.6 相关模型。
- 不引入拖拽排序、第三方 JS/CSS、SMARTS/RDKit 子结构检索。
- 前台只展示已发布路线。
- 继续使用中文版本提交信息，并同步更新根目录 `README.md`。
- 设计规格保存于 `docs/superpowers/specs/`，实施计划保存于 `docs/superpowers/plans/`。

---

### 任务 1：模型变更与迁移

**文件：**
- 修改：`reactions/models.py`
- 创建：`reactions/migrations/0021_routes_functional_groups_key_steps.py`（自动生成）
- 修改：`reactions/tests.py`

**接口：**
- `RouteStep.is_key_step`：BooleanField("关键步骤", default=False)。
- `SyntheticRoute.related_functional_groups`：M2M → `FunctionalGroup`，related_name="routes"，blank。
- `SyntheticRoute.get_key_step_count()`：关键步骤数量。
- `RouteStep` 表单校验：步骤序号从 1 开始且连续。

- [ ] 写失败测试：`V27RouteModelTests` 覆盖关键步骤默认值/计数、官能团关联、序号不连续校验失败。
- [ ] 运行专项测试确认失败（模型字段不存在）。
- [ ] 修改模型 + 生成迁移 + `migrate`。
- [ ] 运行专项测试确认通过。

### 任务 2：Admin 增强

**文件：**
- 修改：`reactions/admin.py`
- 修改：`reactions/forms.py` 或新增步骤表单校验（按现有惯例放置）
- 修改：`reactions/tests.py`

**接口：**
- `SyntheticRouteAdmin`：`related_functional_groups` 加入 `filter_horizontal` 与 `list_filter`；`list_display` 增加关键步骤数、缺图提醒列。
- `RouteStepInline`：增加 `is_key_step` 字段、反应物/产物缩略图只读列。
- `RouteStepAdmin`：`list_display` 增加 `is_key_step`。

- [ ] 写失败测试：`V27RouteAdminTests` 验证官能团选择控件、关键步骤数列、缺图提醒、缩略图列存在。
- [ ] 运行专项测试确认失败。
- [ ] 实现 Admin 与表单校验。
- [ ] 运行专项测试确认通过。

### 任务 3：前台官能团筛选与详情展示

**文件：**
- 修改：`reactions/views/routes.py`
- 修改：`templates/reactions/route_list.html`
- 修改：`templates/reactions/route_detail.html`
- 修改：`static/css/site.css`
- 修改：`reactions/tests.py`

**接口：**
- `RouteListView`：支持 `functional_group` 查询参数（按官能团 slug 过滤），与难度/搜索/排序叠加。
- `RouteDetailView`：上下文增加官能团列表、关键步骤列表。
- 列表页新增官能团筛选下拉，保持选中状态。
- 详情页标题下方显示官能团徽标（链接回列表预选）；关键步骤时间线显示"关键步骤"徽标。

- [ ] 写失败测试：`V27RouteFrontendTests` 验证官能团筛选、徽标展示、未发布不可见、参数叠加。
- [ ] 运行专项测试确认失败。
- [ ] 实现视图、模板与样式。
- [ ] 运行专项测试确认通过。

### 任务 4：文档同步

**文件：**
- 修改：`README.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/organic_chem_hub_update_roadmap.md`
- 修改：`docs/update_roadmap.md`
- 修改：`docs/deploy_linux.md`

- [ ] README：v2.7 标记开发中、功能清单、前台页面描述、版本历史。
- [ ] CHANGELOG：v2.7 章节补充"当前实现范围"。
- [ ] 两个 roadmap：v2.7 章节更新为实现范围，v2.8 前移为下一版本。
- [ ] 部署说明：补充 `0021` 迁移说明。
- [ ] 扫描全部文档中的旧版本状态。

### 任务 5：最终验收与发布

- [ ] 运行 `.venv\Scripts\python.exe manage.py test reactions.tests`（全量）。
- [ ] 运行 `.venv\Scripts\python.exe manage.py check`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py collectstatic --noinput --dry-run`。
- [ ] `git diff --check` 通过。
- [ ] 提交信息：`v2.7: 合成路线扩充 - 官能团筛选、关键步骤与后台维护增强`，推送 `origin/master`。
