# v2.6 学习进度与复习系统实施计划

> **For agentic workers:** 本计划按测试先行执行；每个任务完成后运行对应测试，再进入下一任务。

**目标：** 在 v2.5 专题基础上补齐个人学习闭环：专题进度、复习清单、最近学习记录和个人中心专题聚合。

**架构：** 不新增模型。新增 `reactions/services/progress.py` 服务层集中统计；个人中心（`ProfileView`）和专题详情页（`StudyTopicDetailView`）调用服务层；内联状态切换复用现有 `update_progress` 端点。

**技术栈：** Django 5.2、Django Templates、Bootstrap 5、现有 `site.css`、Django TestCase。

## 全局约束

- 不新增模型，不修改 `StudyProgress` / `StudyTopic` / `ReactionComparison` 表结构。
- 不引入间隔重复算法、提醒推送、邮件通知、站内信。
- 前台只统计已发布专题和已发布关联内容。
- 继续使用中文版本提交信息，并同步更新根目录 `README.md`。
- 设计规格保存于 `docs/superpowers/specs/`，实施计划保存于 `docs/superpowers/plans/`。

---

### 任务 1：进度服务层

**文件：**
- 创建：`reactions/services/progress.py`
- 修改：`reactions/tests.py`

**接口：**
- `topic_progress(user, topic)`：`{total, learned, review, pending, percent}` 或 `None`。
- `topic_status_map(user, topic)`：`{(content_type_id, object_id): status}` 与路线 `{route_id: status}` 合并映射。
- `user_topic_summary(user)`：`[{topic, total, learned, percent}]`，仅已发布专题，按 `sort_order` 排序。
- `review_queue(user)`：待复习记录，`-updated_at` 排序，`select_related("route")`。
- `recent_activity(user, limit=10)`：最近记录，`-updated_at` 排序，`select_related("route")`。

- [ ] 写失败测试：`V26ProgressServiceTests` 覆盖空专题、混合内容总数、只统计已发布、匿名返回 None、排序与过滤。
- [ ] 运行：`.venv\Scripts\python.exe manage.py test reactions.tests.V26ProgressServiceTests`，预期因模块不存在失败。
- [ ] 实现 `progress.py` 服务函数。
- [ ] 运行专项测试，预期通过。

### 任务 2：个人中心复习区块增强

**文件：**
- 修改：`reactions/views/auth.py`
- 修改：`templates/reactions/profile.html`
- 修改：`reactions/tests.py`

**接口：**
- `ProfileView` 增加上下文：`topic_progress_list`（专题进度卡片列表）、`review_queue`（复习清单）、`recent_activity`（最近学习）。
- 模板新增三个区块：专题进度（进度条 + 完成度）、复习清单（全量 + 标记时间 + 所属专题入口）、最近学习（时间线）。
- 现有三栏（待学习/待复习/已学）条目上限调整为 6。

- [ ] 写失败测试：`V26ProfileViewsTests` 验证登录用户看到三个新区块；标记"已学"后专题进度和已学统计同步；匿名被重定向。
- [ ] 运行专项测试确认失败。
- [ ] 实现视图上下文与模板区块（复用 `quick-panel`、progress 组件、badge 样式）。
- [ ] 运行专项测试确认通过。

### 任务 3：专题详情页进度

**文件：**
- 修改：`reactions/views/study.py`
- 修改：`templates/reactions/study_topic_detail.html`
- 修改：`reactions/tests.py`

**接口：**
- `StudyTopicDetailView` 登录用户增加上下文：`topic_progress`（进度条数据）、`status_map`（状态徽标映射）、`topic_has_progress`（总数为 0 时不渲染进度条）。
- 模板：侧栏"我的专题进度"（进度条 + X/Y）；关联反应卡片与路线条目显示状态徽标；每个反应/路线提供内联状态切换表单（复用 `update_progress`，隐藏字段 `content_type` / `reaction` 或 `route`）。
- 匿名用户不渲染进度区块与内联控件（模板用 `user.is_authenticated` 包裹）。

- [ ] 写失败测试：`V26TopicProgressViewsTests` 验证登录用户看到进度条、徽标、内联切换且切换后刷新正确；匿名用户不显示。
- [ ] 运行专项测试确认失败。
- [ ] 实现视图上下文、模板区块与状态徽标样式（`site.css` 少量补充）。
- [ ] 运行专项测试确认通过。

### 任务 4：文档同步

**文件：**
- 修改：`README.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/update_roadmap.md`
- 修改：`docs/organic_chem_hub_update_roadmap.md`
- 修改：`docs/deploy_linux.md`

- [ ] README：当前版本改为 v2.6 开发中，下版本预告，开发文档索引新增 v2.6 设计规格与实施计划，功能概览补充复习系统描述。
- [ ] CHANGELOG：后续规划 v2.6 细化（专题进度、复习清单、最近学习、内联切换），v2.5 保持已完成。
- [ ] 规划文档：v2.6 章节更新为设计规格一致的实现范围。
- [ ] deploy_linux：标题与迁移说明核对（本版本无新迁移，注明无需额外步骤）。
- [ ] 扫描 README、更新日志和规划文档中的旧版本状态。

### 任务 5：最终验收与发布

- [ ] 运行 `.venv\Scripts\python.exe manage.py test reactions.tests`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py check`。
- [ ] 运行 `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`（预期无迁移）。
- [ ] 运行 `.venv\Scripts\python.exe manage.py collectstatic --noinput --dry-run`。
- [ ] 运行 `git diff --check`。
- [ ] 检查 Git 状态，确认不提交 `data/`、`.superpowers/`、`backups/` 和数据库文件。
- [ ] 提交：`v2.6: 学习进度与复习系统 - 专题进度、复习清单与最近学习`。
- [ ] 推送到 `origin master`。
