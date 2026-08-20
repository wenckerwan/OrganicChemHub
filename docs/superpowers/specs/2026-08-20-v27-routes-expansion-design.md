# v2.7 合成路线扩充设计规格

## 1. 版本信息

- 版本：v2.7
- 标题：合成路线扩充 - 官能团筛选、关键步骤与后台维护增强
- 日期：2026-08-20
- 基准版本：v2.6（已完成，2026-08-20）

## 2. 产品目标

让合成路线从"少量展示页"升级为"可训练的复习模块"：用户能按目标官能团快速找到路线、在详情页聚焦关键步骤；管理员能更高效地维护路线步骤、补全图片并扩大路线库规模。

本版本坚持轻量迭代：只做两处小模型变更（`RouteStep.is_key_step` 标记字段、`SyntheticRoute` 关联官能团），不引入第三方前端库、不做拖拽排序、不做 SMARTS 子结构检索。

## 3. 现状盘点（v2.6 结束时已具备）

路线列表：搜索（目标产物/摘要/来源/关联反应名）、难度筛选、排序（步骤数/难度/最近更新）。
路线详情：步骤时间线（试剂/条件/产率/结构式/说明/关联反应标签）、优缺点、来源、相关反应、收藏/进度/笔记、访问统计。
后台：`RouteStepInline` 内联步骤编辑、路线 CSV 导出、完整度展示、批量发布/归档。

## 4. 功能范围

### 4.1 目标官能团筛选

- 模型：`SyntheticRoute` 新增 `related_functional_groups` ManyToMany 关联现有 `FunctionalGroup`（与 `Reaction` 模型同模式）。
- 前台列表页：新增"目标官能团"筛选下拉（`functional_group` 查询参数），与现有难度筛选并列；URL 形如 `/routes/?difficulty=intermediate&functional_group=aldehyde`。
- 前台详情页：目标官能团以徽标形式展示在标题下方，点击可跳转路线列表并预选该官能团。
- 后台：`SyntheticRouteAdmin` 增加 `filter_horizontal` 官能团选择与 `list_filter`。

### 4.2 关键步骤标记

- 模型：`RouteStep` 新增 `is_key_step` BooleanField（"关键步骤"），默认 False。
- 前台详情页：关键步骤在时间线中显示"关键步骤"徽标（金色强调），帮助用户聚焦核心转化。
- 后台：`RouteStepInline` 与 `RouteStepAdmin` 均可编辑该字段；路线列表页 `step_count` 旁增加关键步骤数展示。

### 4.3 后台步骤编辑增强

- 步骤图片预览：`RouteStepInline` 增加反应物/产物结构式缩略图只读列（复用现有 `get_reactant_structure_image_src` / `get_product_structure_image_src`）。
- 步骤序号连续性校验：`RouteStep` 表单校验步骤序号从 1 开始且连续（无缺号）；不连续时给出校验错误，避免前台时间线出现断号。
- 缺图提醒：`SyntheticRouteAdmin.list_display` 增加"缺步骤图"标记（存在步骤但反应物/产物图均缺失时显示提醒图标）。

### 4.4 路线库规模（内容运营，非代码）

- 不新增导入命令；依靠现有 Admin CSV 导出 + 后台批量发布工作流扩充。
- 验收以"至少 20 条已发布路线"为目标，由内容运营完成，代码层提供完整度/缺图提醒支撑。

## 5. 实现边界

- 不引入拖拽排序、第三方 JS/CSS 框架（遵守项目"不引入新前端框架"约束）。
- 不引入 SMARTS 子结构检索、RDKit、Ketcher。
- 不修改 `StudyProgress` / `StudyTopic` / `ReactionComparison` 等 v2.6 相关模型。
- 前台只展示已发布路线。
- 官能团复用现有 `FunctionalGroup` 模型，不新建模型。

## 6. 测试验收标准

### 模型与后台

- `RouteStep.is_key_step` 可创建、编辑，默认 False。
- `SyntheticRoute.related_functional_groups` 可关联多个官能团。
- 步骤序号不连续时保存报错（如 1、3 缺 2）。
- Admin 路线列表显示关键步骤数、缺图提醒；内联步骤可编辑关键步骤并预览图片。

### 前台

- 路线列表按官能团筛选正确，与其他筛选条件可叠加。
- 路线详情显示目标官能团徽标和关键步骤徽标。
- 未发布路线仍不可见。

### 回归

- 现有 `reactions.tests` 全部通过。
- `manage.py check` 通过。
- `makemigrations --check --dry-run` 无未生成迁移（含新迁移 0021）。
- `git diff --check` 通过。

## 7. 实施顺序

1. 模型变更（`is_key_step` + `related_functional_groups`）、迁移与模型测试。
2. 步骤序号校验 + Admin 增强（官能团选择、关键步骤数、缺图提醒、图片预览）。
3. 前台官能团筛选（列表）+ 详情页官能团/关键步骤展示 + 测试。
4. 文档同步（README / CHANGELOG / roadmap / 部署说明）。
5. 最终验收（全量测试、check、迁移检查、collectstatic、提交推送）。
