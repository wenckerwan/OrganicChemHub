# v2.5 考研专题学习实施计划

> **For agentic workers:** 本计划按测试先行执行；每个任务完成后运行对应测试，再进入下一任务。

**目标：** 新增考研专题、易混反应对比和个人复习入口，复用现有反应、路线、学习进度与访问统计能力。

**架构：** 新增 `StudyTopic` 和 `ReactionComparison` 两个内容模型，使用 Django Admin 管理。前台新增专题和对比列表/详情视图，关联内容只查询已发布对象；个人中心扩展复习区块，不复制现有 `StudyProgress` 模型。

**技术栈：** Django 5.2、Django Templates、Bootstrap 5、现有 `site.css`、SQLite 迁移、Django TestCase。

## 全局约束

- 不引入 SMILES、RDKit、Ketcher、结构式编辑器或子结构检索。
- 不移动 `organic_chem_hub/`、`reactions/`、`templates/`、`static/`。
- 前台只展示已发布专题、对比和已发布关联内容。
- 继续使用中文版本提交信息，并同步更新根目录 `README.md`。
- 设计规格保存于 `docs/superpowers/specs/`，实施计划保存于 `docs/superpowers/plans/`。

---

### 任务 1：新增专题和反应对比模型

**文件：**
- 修改：`reactions/models.py`
- 创建：`reactions/migrations/0019_study_topics_and_comparisons.py`
- 测试：`reactions/tests.py`

**接口：**
- 产出 `StudyTopic`、`ReactionComparison` 模型及其发布查询能力。
- `ReactionComparison` 的两个反应必须不同，支持人名反应或常见有机反应。

- [ ] 写失败测试：测试专题字段、发布状态、关联关系和对比不能选择同一个反应。
- [ ] 运行：`.venv\Scripts\python.exe manage.py test reactions.tests.V25ModelTests`，预期因模型不存在失败。
- [ ] 添加模型、校验方法和迁移。
- [ ] 运行专项测试，预期通过。
- [ ] 运行 `manage.py makemigrations --check --dry-run`，预期无未生成迁移。

### 任务 2：注册 Django Admin

**文件：**
- 修改：`reactions/admin.py`
- 修改：`reactions/tests.py`

**接口：**
- Admin 注册 `StudyTopicAdmin` 和 `ReactionComparisonAdmin`。
- 提供状态、排序、搜索、关联内容和发布/归档操作。

- [ ] 写失败测试：登录后台访问两个列表页，验证 200、中文模型名称和状态字段存在。
- [ ] 运行专项测试确认失败。
- [ ] 实现 Admin 配置，使用现有 `PublicationActionMixin` 或同等发布操作。
- [ ] 运行专项测试确认通过。

### 任务 3：专题前台页面

**文件：**
- 修改：`reactions/views/study.py`
- 修改：`reactions/urls.py`
- 创建：`templates/reactions/study_topic_list.html`
- 创建：`templates/reactions/study_topic_detail.html`
- 修改：`reactions/tests.py`

**接口：**
- `StudyTopicListView`：搜索、分页、只显示已发布专题。
- `StudyTopicDetailView`：显示简介、目标、考点、已发布关联反应/路线和访问量。
- URL 名称：`study_topic_list`、`study_topic_detail`。

- [ ] 写失败测试：草稿专题不可见，已发布专题可搜索、可打开详情、显示关联内容和访问量。
- [ ] 运行专项测试确认失败。
- [ ] 实现查询、URL、模板和前台样式。
- [ ] 运行专项测试确认通过。

### 任务 4：易混反应对比前台页面

**文件：**
- 修改：`reactions/views/study.py`
- 修改：`reactions/urls.py`
- 创建：`templates/reactions/reaction_comparison_list.html`
- 创建：`templates/reactions/reaction_comparison_detail.html`
- 修改：`reactions/tests.py`

**接口：**
- `ReactionComparisonListView`：搜索、分页、只显示已发布对比。
- `ReactionComparisonDetailView`：并列显示两个已发布反应、底物/条件/产物/考法/易错点和访问量。
- URL 名称：`reaction_comparison_list`、`reaction_comparison_detail`。

- [ ] 写失败测试：草稿对比不可见；已发布对比详情显示两侧反应名称和对比字段。
- [ ] 运行专项测试确认失败。
- [ ] 实现视图、模板和响应式并列布局。
- [ ] 运行专项测试确认通过。

### 任务 5：首页和个人中心复习入口

**文件：**
- 修改：`templates/reactions/home.html`
- 修改：`reactions/views/auth.py`
- 修改：`templates/reactions/profile.html`
- 修改：`static/css/site.css`
- 修改：`reactions/tests.py`

**接口：**
- 首页增加专题学习和易混反应入口。
- 个人中心继续复用 `StudyProgress`，增加待学习、已学、待复习列表/数量及专题入口。

- [ ] 写失败测试：首页包含两个新入口；登录用户个人中心显示复习区块；匿名用户仍被登录保护。
- [ ] 运行专项测试确认失败。
- [ ] 实现上下文查询、模板区块和移动端样式。
- [ ] 运行专项测试确认通过。

### 任务 6：后台与前台 UI 细化、文档同步

**文件：**
- 修改：`static/css/admin.css`
- 修改：`README.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/update_roadmap.md`
- 修改：`docs/organic_chem_hub_update_roadmap.md`
- 修改：`docs/organic_chem_hub_development_doc.md`
- 修改：`docs/deploy_linux.md`

- [ ] 补充专题卡片、对比表格、复习区块和 Admin 表单样式。
- [ ] 更新当前版本、文档索引、v2.5 功能和 `0020` 或实际迁移编号说明。
- [ ] 更新服务器部署命令，保留旧迁移清理说明。
- [ ] 扫描 README、更新日志和规划文档中的旧版本状态。

### 任务 7：最终验收与发布

- [ ] 运行 `.venv\Scripts\python.exe manage.py test reactions.tests`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py check`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py collectstatic --noinput --dry-run`。
- [ ] 运行 `git diff --check`。
- [ ] 检查 Git 状态，确认不提交 `data/`、`.superpowers/` 和数据库文件。
- [ ] 提交：`v2.5: 考研专题学习 - 专题分类、易混反应对比与复习入口`。
- [ ] 推送到 `origin master`。

