# v3.0 公开稳定版实施计划

> **For agentic workers:** 本计划按测试先行执行；每个任务完成后运行对应测试，再进入下一任务。

**目标：** 打通内容上线工作流：占位图生成让 85 条草稿反应可发布，图片维护工具支持筛选与批量操作，内容就绪报告指导补图，发布流程写入审计。

**架构：** 零模型变更、零迁移。新增 `reactions/services/placeholder.py` 与 `reactions/services/readiness.py`，增强图片维护工具与 `publish_ready_content` 命令，扩展仪表盘计数。

**技术栈：** Django 5.2、Django Admin、Django TestCase、管理命令。

## 全局约束

- 零模型变更、零迁移、不引入第三方库。
- 前台无改动；全部为后台工具与管理命令改动。
- 占位图路径含 `placeholder/` 目录段，与真实上传图区分。
- 继续使用中文版本提交信息，并同步更新根目录 `README.md`。
- 设计规格保存于 `docs/superpowers/specs/`，实施计划保存于 `docs/superpowers/plans/`。

---

### 任务 1：占位图服务 + 图片维护工具增强

**文件：**
- 创建：`reactions/services/placeholder.py`
- 修改：`reactions/admin_tools.py`（`image_maintenance_view` 筛选 + 批量生成）
- 修改：`templates/admin/reactions/images.html`（筛选下拉 + 批量按钮 + 分页）
- 修改：`reactions/tests.py`

**接口：**
- `placeholder.equation_svg(title)` → SVG 文本（含标题与"待补充"提示）。
- `placeholder.thumbnail_svg(title)` → SVG 文本（品牌色 + 首字）。
- `placeholder.placeholder_for(instance)` → 生成两图并绑定字段，返回绑定字段名列表。
- `image_maintenance_view`：GET 支持 `?missing=equation|thumbnail|mechanism` 筛选；POST `generate_placeholders` 批量生成（写 OpLog + ContentBatch）。

- [ ] 写失败测试：`V30PlaceholderTests` 覆盖 SVG 内容、绑定字段、文件存在、筛选、批量生成记录。
- [ ] 运行专项测试确认失败。
- [ ] 实现 placeholder.py + 视图 + 模板。
- [ ] 运行专项测试确认通过。

### 任务 2：内容就绪报告命令

**文件：**
- 创建：`reactions/services/readiness.py`
- 创建：`reactions/management/commands/content_readiness_report.py`
- 修改：`reactions/tests.py`

**接口：**
- `readiness.summary()` → {模型: {total, ready, missing_fields, missing_images, placeholder_count}}。
- `readiness.export_rows()` → 逐条字典列表。
- 命令 `content_readiness_report`：`--export path.csv` 导出；无参时控制台统计。

- [ ] 写失败测试：`V30ReadinessTests` 覆盖统计准确性与 CSV 行内容。
- [ ] 运行专项测试确认失败。
- [ ] 实现 readiness.py + 命令。
- [ ] 运行专项测试确认通过。

### 任务 3：发布流程闭环

**文件：**
- 修改：`reactions/management/commands/publish_ready_content.py`
- 修改：`reactions/admin_tools.py`（仪表盘 `placeholders_pending` 计数）
- 修改：`templates/admin/reactions/dashboard.html`
- 修改：`reactions/tests.py`

**接口：**
- `publish_ready_content` 发布后写 OpLog（action=`publish`）与 ContentBatch（kind=`publish`）。
- 仪表盘上下文增加 `placeholders_pending`（占位图待替换数）。

- [ ] 写失败测试：`V30PublishLoopTests` 覆盖命令写批次与仪表盘计数。
- [ ] 运行专项测试确认失败。
- [ ] 实现命令与仪表盘。
- [ ] 运行专项测试确认通过。

### 任务 4：文档同步

- 更新 `docs/CHANGELOG.md`（v3.0 章节 + 实现范围）。
- 更新 `docs/organic_chem_hub_update_roadmap.md` 与 `docs/update_roadmap.md`（v3.0 改为开发中/已交付）。
- 更新根目录 `README.md`（版本状态 + 历史表）。
- 更新 `docs/deploy_linux.md`（v3.0 零迁移说明，无需额外步骤）。

### 任务 5：最终验收与发布

- [ ] 全量测试 `reactions.tests` 通过。
- [ ] `manage.py check` 无问题。
- [ ] `makemigrations --check --dry-run` 无未生成迁移。
- [ ] `collectstatic --noinput` 同步。
- [ ] `git diff --check` 通过。
- [ ] 提交：`v3.0: 公开稳定版 - 占位图工作流与内容就绪报告`，推送 `origin/master`。
