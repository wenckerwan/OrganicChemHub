# OrganicChemHub 更新日志

> 版本历史与更新规划

---

## 更新规划

### v1.6 — 结构式检索（待开发）

- 用户输入分子 SMILES 搜索包含该子结构的反应
- 官能团搜索（利用已有 `FunctionalGroup.smarts`）
- 搜索结果展示匹配的结构式高亮

### v1.7 — 学习专题（待开发）

- 按主题归类（碳链增长、官能团转化、氧化还原、重排）
- 易混反应对比页
- "考研高频"专题入口
- 学习路径建议

### 远期规划

- 合成路线扩充到 20+ 条
- 反应库扩充到 100+ 条
- RDKit 子结构检索
- Ketcher 后台结构编辑器
- 批量导入导出完善
- PostgreSQL 生产数据库迁移

---

## 版本历史

### 1.5 反馈升级与站内消息（2026-07-29）

- 反馈系统升级：新增类型分类（内容纠错/功能建议/数据补充/使用问题）、状态流转（待处理/处理中/已处理/已关闭）、管理员公开回复、管理员内部备注
- **站内消息系统**：新增 Message 模型，消息中心页面 `/messages/`，按类型筛选，全部已读，未读红点
- **公告自动推送**：发布公告时自动向所有注册用户发送站内消息
- **反馈回复通知**：管理员回复反馈或变更状态时，自动向用户发送消息通知
- 个人中心新增「我的反馈」记录，显示类型/状态/管理员回复
- 导航栏新增信封图标 + 未读数量红点

### 1.4 用户体系与个性化（2026-07-29）

- 用户注册/登录/退出（Django 内置 auth + 自定义模板）
- 收藏功能：反应/路线详情页 ❤️ 切换收藏，个人中心展示收藏列表
- 私人笔记：详情页底部笔记框（仅自己可见）
- 学习进度：已学/待复习/待学习三种状态，详情页下拉切换
- 个人中心：收藏数/笔记数/已学数/待复习数统计
- 版本号统一管理：`APP_VERSION` 全局变量，全站自动同步

### 1.3 公告弹窗与意见反馈（2026-07-29）

- 公告栏关闭按钮、重要公告弹窗、置顶功能、显示起止时间
- 意见反馈表单（名称/邮箱/内容），仅后台可见
- 导航栏「反馈」入口链接

### 1.2 后台工具增强（2026-07-29）

- **CSV 导出**：Reaction、SyntheticRoute、LearningResource 三个列表页新增「导出选中为 CSV」操作，一键下载为 Excel 可打开的 UTF-8 CSV 文件。
- **内容质量仪表盘**：后台新增 `/admin/reactions/reaction/dashboard/` 页面，卡片展示总反应数、已发布/草稿/归档数、缺图片/摘要/条件/来源的反应数量，以及最近更新的反应列表。
- **CSV 导入补充字段**：`import_reactions_csv` 命令新增 `aliases`、`mechanism`、`scope`、`limitations` 字段覆盖。
- Git 同步流程完成，本地开发目录迁移到 `D:\code_files\OrganicChemHub_dsv`。

### 0.9 彻底移除 SMILES（2026-07-29）

- **数据库删除所有 SMILES 字段**：`Reaction.equation_smiles`、`SyntheticRoute.target_smiles`、`RouteStep.reactant_smiles`、`RouteStep.product_smiles` 全部移除。
- **后台完全改为图片上传**：删除旧版 `structure_image`/`structure_image_url` 折叠区，三个图片字段（反应方程式、反应机理、缩略图）各自独立分组，每个带预览 + 文件选择 + help_text 指引。
- **`get_equation_img_src()` 新增 fallback**：当 `equation_img` 为空时自动读取 `structure_image_url`，保证旧数据平滑过渡。
- **`get_thumbnail_img_src()` 新增 fallback**：缩略图为空时降级使用 `equation_img`。
- **清除所有 SMILES 代码引用**：views.py、admin.py、fixture 全部清理。
- 44 项测试全部通过，代码零 SMILES 引用。

### 0.8 内容迁移（2026-07-29）

- 安装 RDKit 和 NumPy（`rdkit-pypi>=2022.9`、`numpy<2`、`Pillow>=10.0`），更新 requirements.txt。
- 编写 `scripts/generate_reaction_images.py`：批量解析非空 SMILES，使用 RDKit 生成 SVG 结构式图片。
- 生成 26 个反应的 equation SVG + thumbnail SVG（800×350 / 400×175 viewBox），存入 `static/images/reactions/`。
- 2 个 Wittig 反应因 SMILES 含非标准 `CPPh3` 缩写无法解析，手动从旧 PNG 迁移。
- 编写 `import_reaction_images` 管理命令：扫描命名文件 `reaction_{slug}_equation.svg`，自动匹配数据库记录并写入 `structure_image_url`。
- 18 个无 SMILES 的反应暂未生成图片，留待手动补全。

### 0.7 前端展示改造（2026-07-29）

- 清理 base.html：确认无任何化学渲染库引用，仅保留 Bootstrap 5.3.3 CSS/JS 和 Bootstrap Icons，页脚版本号更新至 0.7。
- 清理死 CSS：删除 `.mini-smiles`、`.reaction-result-item__smiles`、`.structure-viewer__raw`、`.molecule-tile`、`.reaction-arrow` 及其所有子选择器，共减少约 100 行无用代码。
- 所有结构式图片增加 `onerror` 加载失败兜底。
- route_detail.html 完全移除 SMILES 条件判断和 `smiles=` 参数传递。
- 移动端适配增强：`<576px` 时缩略图取消左侧间距，全部图片保持 `max-width: 100%`。

### 0.6 后台与数据库改造（2026-07-29）

- Reaction 模型新增三个图片字段：`equation_img`（反应方程式）、`mechanism_img`（反应机理）、`thumbnail_img`（缩略图）。
- 上传自动重命名，按 `reaction_{slug}_{type}.{ext}` 格式存储到 `media/reaction_images/`。
- 后台管理界面重构：旧版 structure_image 字段折叠隐藏，新增分组图片上传控件和实时预览。
- 后台列表页增加缩略图列 `admin_thumbnail`。
- 前台模板移除 SMILES 文本展示，替换为缩略图和方程式图片。
- 新增 SMILES 备份脚本 `backup_smiles`。

### 0.5 图片规范与静态资源整理（2026-07-29）

- 制定图片文件命名规则，规范 Reaction、SyntheticRoute、RouteStep 三模型的 SVG 命名。
- 规划服务器图片存储目录结构：`static/images/reactions/`、`static/images/routes/`。
- 确定图片统一规格：SVG 格式、Arial 字体、透明背景、键长/字号标准。
- 选定 ChemDraw 为绘图工具，编写管理员图片制作规范文档。

### 0.37 图片结构式与后台维护

- 结构式展示改为图片优先，不再依赖在线 SMILES 渲染。
- 反应、路线目标产物、路线步骤支持后台上传结构式图片或填写图片 URL。
- 后台增加结构式图片预览和配置状态。

### 0.36 查询页与考研反应扩充

- 人名反应查询页改为左侧滚动目录、右侧结果内容区的资料库布局。
- 新增 exam_reactions fixture，补充 32 条考研常见人名反应。

### 0.35 UI 与结构式展示

- 前台首页、导航、卡片和详情页视觉升级。
- 后台管理增加 OrganicChemHub 标题和基础主题样式。

### 0.3 搜索与分类增强

- 人名反应支持官能团筛选、考研高频快捷筛选。
- 搜索结果关键词高亮、空结果推荐、分页保留筛选条件。

### 0.25 首次部署与资料索引

- 首次部署引导页、宝塔面板部署文档。
- 常见人名反应 fixture（common_reactions）。
- 学习资料索引模型和页面。

### 0.2 内容维护增强

- 发布前校验必填字段、后台列表显示内容完整度。
- 批量发布/归档完整内容。

### 0.1 基础功能

- Django Admin 后台增删改查。
- 首页、反应列表/详情、路线列表/详情。
- 公开页面只显示已发布内容、基础自动化测试。

### 1.7 后台内容管理重构（2026-08-02）

- 人名反应和常见有机反应拆成两套内容库：`NamedReaction` 与 `GeneralReaction`。
- 新增两套分类：`NamedReactionCategory` 与 `GeneralReactionCategory`。
- Django Admin 支持新内容库的筛选、搜索、图片预览、完整度展示、批量发布/归档和 CSV 导出。
- 专用后台工具页新增内容质量仪表盘、CSV 导入、图片维护、消息群发、消息清理、资料上传/登记。
- 前台人名反应页优先读取新内容库，常见有机反应新增独立列表和详情页。
- 公告推送增加去重字段 `message_sent_at`；反馈回复和状态变化会向用户发送站内消息。
- 新增 `python manage.py setup_admin_roles`，用于初始化“内容编辑员”和“运营员”角色。
