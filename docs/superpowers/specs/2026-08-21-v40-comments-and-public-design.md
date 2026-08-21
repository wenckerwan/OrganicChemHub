# v4.0 评论与公开化设计规格

## 1. 版本信息

- 版本：v4.0
- 标题：评论/社区功能与 SEO 公开化
- 日期：2026-08-21
- 基准版本：v3.0（已完成，2026-08-20）

## 2. 产品目标

v3.0 打通了"草稿 → 占位图 → 发布 → 前台可见"的上线工具链，但前台内容库尚未实际填充。v4.0 目标：

1. 让前台形成基础社区互动：登录用户可在内容详情页发表评论与回复，管理员可审核管理。
2. 让网站可被搜索引擎收录并友好分享：sitemap、robots、独立 meta、错误页。
3. 复用 v3.0 已交付的上线工具完成内容库填充，使公开网站有真实内容可看、可评。

## 3. 现状盘点（2026-08-21）

- 登录注册已实现：`accounts/`（Django auth）＋ `reactions/urls.py` 的 `register/`。
- 用户互动模型已统一走 GFK：`Favorite`、`Note`、`StudyProgress`（迁移 `0020_user_tools_gfk`）。
- 站内消息 `Message` 已存在（v2.8 群发），评论不与其耦合。
- 前台模板体系成熟：`templates/reactions/*.html` 统一继承 `base.html`。
- 审计体系成熟：`reactions/services/audit.py`（`log_operation`/`record_batch`）。
- 内容库：人名反应 43（已发布 0）、常见反应 42（已发布 0）、路线 1、专题 0、对比 0、资料 344。

## 4. 功能设计

### 4.1 评论模型（Comment）

复用 GFK 模式，与 Favorite/Note 一致：

| 字段 | 类型 | 说明 |
|------|------|------|
| user | FK(User) | 评论者，related_name="comments" |
| content_type / object_id | FK / PositiveInteger | 通用内容关联 |
| content_object | GenericForeignKey | 关联任意可评论内容 |
| body | TextField | 评论正文，纯文本（保留换行） |
| parent | FK(Comment, null, blank) | 父评论，实现回复（限制一层） |
| is_hidden | BooleanField(default=False) | 管理员隐藏标记 |
| created_at / updated_at | DateTimeField | 时间戳 |

约束：

- 评论正文非空，`clean()` 校验长度上限（如 2000 字）。
- 回复只能回复顶级评论（parent.parent 为空），保持一层结构简单。
- 隐藏评论默认不展示；作者本人可见"已隐藏"提示（可选，首版不做）。
- 删除策略：不物理删除，统一用 `is_hidden` 隐藏，保留审计线索。

### 4.2 前台评论区

- 详情页（人名反应、常见反应、路线、专题、易混对比）底部统一渲染评论区。
- 登录用户：表单（正文 + 提交）；可对顶级评论点"回复"（内联表单）。
- 匿名用户：显示"登录后参与评论"提示（链接到 `accounts/login/`）。
- 展示：评论正序（旧→新），回复缩进展示在父评论下；显示作者名与时间。
- 提交采用普通表单 POST，成功后重定向回详情页（锚点 `#comments`）。
- 渲染评论数在详情页标题区显示（"评论 (n)"）。

### 4.3 后台评论管理

- `CommentAdmin`：
  - list_display：正文摘要、用户、内容对象、is_hidden、created_at。
  - list_filter：is_hidden、content_type、created_at。
  - search_fields：body、user__username。
  - 批量操作：隐藏选中、恢复选中（写 OpLog）。
- 详情页隐藏操作同样写 OpLog（action="hide_comment"/"unhide_comment"）。

### 4.4 个人中心"我的评论"

- 个人中心新增区块：我的评论列表（最新在前），显示关联内容链接、正文摘要、隐藏状态。
- 匿名/未登录不显示。

### 4.5 SEO 公开化

- `django.contrib.sitemaps`：
  - `StaticViewSitemap`：首页、列表页（人名反应/常见反应/路线/专题/对比/资料）。
  - 内容 Sitemap：各内容库已发布对象（`lastmod` 用 `updated_at`）。
  - URL：`/sitemap.xml`；robots：`/robots.txt`（Sitemap 指向）。
- 详情页 meta：
  - `<title>` 已有（模板各自设置），补充 `<meta name="description">`（从 summary/简介截断）、`<link rel="canonical">`、OG 标签（og:title/og:description/og:type/og:url）。
  - 统一实现：`reactions/templatetags/seo_extras.py` 或 base.html 区块 + 各详情页模板提供 `meta_description` 上下文。
- 错误页：
  - `404.html` / `500.html` 自定义模板（友好文案 + 返回首页按钮）。
  - 开发环境 DEBUG=False 时生效；测试用 `override_settings(DEBUG=False)` 或 handler 视图。

## 5. 不做什么

- 评论点赞/踩、编辑/删除自己的评论（首版仅隐藏）、富文本、表情。
- 第三方评论系统。
- 注册策略调整（保持现状）。
- 评论通知/站内信联动（预留，不做）。

## 6. 数据与迁移

- 新增模型 `Comment`，迁移 `0023_comment`。
- 评论索引：`(content_type, object_id, created_at)`、`parent`。

## 7. 验收标准

- 登录用户可在任意详情页发表评论与回复；匿名用户看到登录引导。
- 管理员可在后台筛选、隐藏/恢复评论，操作写入 OpLog。
- 个人中心展示我的评论。
- sitemap.xml 列出全部已发布内容 URL；robots.txt 指向 sitemap。
- 详情页有独立 description 与 canonical；错误页友好。
- 全量测试通过（新增 V40 专项测试）。
