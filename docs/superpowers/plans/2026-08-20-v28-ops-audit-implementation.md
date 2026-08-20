# v2.8 运营与审计实施计划

> **For agentic workers:** 本计划按测试先行执行；每个任务完成后运行对应测试，再进入下一任务。

**目标：** 让网站进入稳定运营状态：内容批次记录、操作日志覆盖、导入错误报告下载、备份恢复文档。

**架构：** 新增一个模型 `ContentBatch`（迁移 `0022_content_batch`）与服务层 `reactions/services/audit.py`；`OpLog` 模型不变仅扩大写入覆盖；错误报告复用 CSV 导出模式。

**技术栈：** Django 5.2、Django Admin、Django TestCase。

## 全局约束

- 只新增 `ContentBatch` 模型；`OpLog` 不加字段。
- 不引入 Celery、后台任务、邮件通知、第三方库。
- 前台无任何改动；本版本全部为后台与文档改动。
- 继续使用中文版本提交信息，并同步更新根目录 `README.md`。
- 设计规格保存于 `docs/superpowers/specs/`，实施计划保存于 `docs/superpowers/plans/`。

---

### 任务 1：模型与服务层

**文件：**
- 修改：`reactions/models.py`（新增 `ContentBatch`）
- 创建：`reactions/migrations/0022_content_batch.py`（自动生成）
- 创建：`reactions/services/audit.py`
- 修改：`reactions/tests.py`

**接口：**
- `ContentBatch.Kind`：import/publish/archive/cleanup/other。
- `ContentBatch` 字段：kind、operator(FK, SET_NULL, null)、summary、detail、object_count、created_at(auto_now_add)；`Meta.ordering = ["-created_at"]`。
- `audit.log_operation(user, action, model_name, object_repr, detail="", ip=None)` → 创建 OpLog。
- `audit.record_batch(kind, operator, summary, objects, detail="")` → 创建 ContentBatch，objects 为名称列表，object_count 取其长度，detail 存 JSON（截断 2000 字符）。

- [ ] 写失败测试：`V28AuditModelTests` 覆盖 ContentBatch 创建/排序、log_operation 字段、record_batch 数量与 JSON 截断。
- [ ] 运行专项测试确认失败（模型/服务不存在）。
- [ ] 实现模型 + 生成迁移 + migrate + 实现 audit.py。
- [ ] 运行专项测试确认通过。

### 任务 2：日志与批次接入

**文件：**
- 修改：`reactions/admin.py`（PublicationActionMixin、OpLogAdmin、注册 ContentBatchAdmin）
- 修改：`reactions/admin_tools.py`（CSV 导入写 OpLog + ContentBatch）
- 修改：`reactions/tests.py`

**接口：**
- `PublicationActionMixin._publish_selected` / `_archive_selected`：成功后写 OpLog 与 ContentBatch。
- CSV 导入成功：写 OpLog（action=csv_import）与 ContentBatch（kind=import）。
- `OpLogAdmin.list_filter` 增加 `action`；`date_hierarchy = "created_at"`。
- 新增 `ContentBatchAdmin`：list_display（kind/operator/summary/object_count/created_at）、list_filter（kind/operator）、search_fields（summary）、readonly detail 展示。

- [ ] 写失败测试：`V28BatchRecordingTests` 验证批量发布/归档/CSV 导入后 OpLog 与 ContentBatch 存在且计数正确、后台页面可访问。
- [ ] 运行专项测试确认失败。
- [ ] 实现接入。
- [ ] 运行专项测试确认通过。

### 任务 3：导入错误报告

**文件：**
- 修改：`reactions/admin_tools.py`（结构化 errors + 下载端点）
- 修改：`reactions/admin.py`（URL 注册）
- 修改：`reactions/templates/admin/reactions/import.html`（下载按钮）
- 修改：`reactions/tests.py`

**接口：**
- `import_reactions_from_csv` 的 errors 元素改为 dict：`{"line": int, "fields": [...], "raw": str, "reason": str}`；缺失字段错误 fields 列出，校验失败 reason 为异常文本，raw 为该行原始值摘要。
- 下载端点：`/admin/reactions/import/errors/download/`（POST 携带 JSON errors 或按导入会话），返回 CSV 附件（列：行号、错误字段、原始值、建议修复）。
- 导入结果区展示错误条数，并提供下载按钮（errors 非空时可见）。

- [ ] 写失败测试：`V28ImportReportTests` 验证结构化 errors 字段、下载端点返回附件且含四列。
- [ ] 运行专项测试确认失败。
- [ ] 实现。
- [ ] 运行专项测试确认通过。

### 任务 4：文档同步

**文件：**
- 修改：`README.md`、`docs/CHANGELOG.md`、`docs/organic_chem_hub_update_roadmap.md`、`docs/update_roadmap.md`
- 修改：`docs/deploy_linux.md`（新增"备份与恢复"章节：数据库备份、media 备份、git 回滚、更新检查清单）

**提交信息：** `v2.8: 运营与审计 - 内容批次记录、操作日志覆盖与导入错误报告`

### 任务 5：最终验收发布

- 全量测试 `reactions.tests` 通过；`manage.py check`、`makemigrations --check --dry-run`、`collectstatic --dry-run`、`git diff --check` 全部通过。
- 提交推送 `origin/master`，工作区干净。
