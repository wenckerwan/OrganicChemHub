# v2.8 运营与审计设计规格

## 1. 版本信息

- 版本：v2.8
- 标题：运营与审计 - 内容批次记录、操作日志覆盖与导入错误报告
- 日期：2026-08-20
- 基准版本：v2.7（已完成，2026-08-20）

## 2. 产品目标

让网站进入稳定运营状态：管理员能追踪一次导入或发布影响了哪些内容、批量操作留下审计痕迹、导入失败数据可下载修复、服务器更新前后有清晰备份与回滚步骤。

本版本坚持轻量迭代：只新增一个模型（`ContentBatch` 内容批次），`OpLog` 模型保持原样仅扩大覆盖；错误报告复用现有 CSV 导出模式，不引入第三方库。

## 3. 现状盘点（v2.7 结束时已具备）

- `OpLog` 模型已存在（操作人/操作/模型/对象/详情/IP/时间），但只在站内消息群发和消息清理两处写入；批量发布/归档、CSV 导入均无审计。
- CSV 导入（`reactions/admin_tools.py`）返回 `{created, updated, skipped, errors}`，`errors` 为纯文本列表（含行号），仅在页面一次性展示，无法下载。
- 后台已有 CSV 导出（反应/路线/资料）、内容质量仪表盘、批量发布/归档 Action。
- 部署文档已有更新流程说明，但无独立备份/恢复/回滚章节。

## 4. 功能范围

### 4.1 内容批次记录（新模型 `ContentBatch`）

- 模型字段：`kind`（import/publish/archive/cleanup/other）、`operator`（FK User）、`summary`（摘要）、`detail`（JSON 文本：受影响对象名称列表，截断保存）、`object_count`（影响数量）、`created_at`。
- 接入点：批量发布/归档成功时、CSV 导入成功时、消息清理时创建批次记录。
- 后台：`ContentBatchAdmin` 列表展示（类型/操作人/数量/时间）、按类型与操作人筛选、搜索摘要。

### 4.2 操作日志覆盖增强（`OpLog` 模型不变）

- 新增服务 `reactions/services/audit.py`：`log_operation(user, action, model_name, object_repr, detail="", ip=None)` 统一写入入口。
- `PublicationActionMixin._publish_selected` / `_archive_selected` 写 OpLog（action=batch_publish / batch_archive，detail 含发布/跳过摘要）。
- CSV 导入写 OpLog（action=csv_import，detail 含新增/更新/跳过/错误数）。
- `OpLogAdmin` 增强：`list_filter` 增加 `action`，`date_hierarchy` 使用 `created_at`。

### 4.3 导入错误报告下载

- `import_reactions_from_csv` 的 `errors` 改为结构化列表：`{line, fields, raw, reason}`（行号、错误字段、原始行值摘要、建议修复方式）。
- 页面展示保持现有样式，另在导入结果区提供"下载错误报告（CSV）"按钮。
- 新增下载端点：按导入会话渲染 CSV（列：行号、错误字段、原始值、建议修复），`Content-Disposition` 附件下载。

### 4.4 备份与恢复文档

- `docs/deploy_linux.md` 新增"备份与恢复"章节：数据库备份（生产库 dump / SQLite 拷贝）、`media` 文件备份、git 版本回滚流程、更新前后检查清单。

## 5. 实现边界

- 不新增导入命令、不改造现有 CSV 导出。
- 不引入 Celery、后台任务或邮件通知。
- `OpLog` 模型不加字段，批次记录独立成表；`ContentBatch.detail` 用 JSON 文本承载对象摘要，不建批次明细表。
- 前台无任何改动，本版本全部为后台与文档改动。

## 6. 测试验收标准

### 模型与日志

- `ContentBatch` 创建/字段/排序正确；迁移 `0022_content_batch` 可应用。
- `log_operation` 写入 OpLog 字段正确；批量发布/归档/导入后 OpLog 与 ContentBatch 记录存在且数量正确。

### 导入错误报告

- 错误 CSV 下载端点返回附件；内容包含行号、错误字段、原始值、建议修复。

### 验收标准（对应 roadmap）

- 管理员能追踪一次导入或发布影响了哪些内容（批次记录 + 操作日志）。
- 导入失败数据能被下载后修复（结构化错误 + CSV 下载）。
- 服务器更新前后有清晰的备份与回滚步骤（文档章节）。
