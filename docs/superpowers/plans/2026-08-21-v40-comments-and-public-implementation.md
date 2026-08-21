# v4.0 评论与公开化实施计划

> **For agentic workers:** 本计划按测试先行执行；每个任务完成后运行对应测试，再进入下一任务。

**目标：** 前台形成基础社区互动（评论/回复/审核），网站可被搜索引擎收录（sitemap/robots/meta/错误页）。

**架构：** 新增模型 `Comment`（迁移 `0023_comment`）复用 GFK 互动模式；前台评论区 + 后台审核 + 个人中心；SEO 用 `django.contrib.sitemaps` + 模板 meta 区块。

---

## 任务 1：Comment 模型 + 迁移

- 新增 `Comment` 模型（user/content_type/object_id/content_object/body/parent/is_hidden/created_at/updated_at），GFK 模式与 Favorite 一致；`clean()` 校验正文非空、回复仅限一级。
- 生成迁移 `0023_comment` 并应用。
- 测试：`V40CommentModelTests`（创建、回复层级校验、正文长度校验、默认排序、隐藏过滤）。

## 任务 2：前台评论区

- 详情页（人名反应、常见反应、路线、专题、易混对比）底部评论区：登录可发表/回复，匿名显示登录引导，正序展示 + 回复缩进 + 评论计数。
- 实现：`reactions/services/comments.py`（`comment_form_for`、`visible_comments`、`create_comment`）+ `reactions/forms.py` 增加 `CommentForm` + 详情视图 POST 处理 + 共享模板 `templates/reactions/_comments.html`。
- 测试：`V40CommentFrontendTests`（登录发表、回复、匿名引导、隐藏评论不显示、评论数）。

## 任务 3：后台评论管理

- `CommentAdmin`：列表/筛选/搜索 + 批量隐藏/恢复（写 OpLog）。
- 测试：`V40CommentAdminTests`（批量隐藏写 OpLog、筛选、隐藏后前台不可见）。

## 任务 4：个人中心"我的评论"

- 个人中心新增我的评论列表（关联内容链接、正文摘要、隐藏状态）。
- 测试：`V40ProfileCommentsTests`（登录可见、匿名不可见、最新在前）。

## 任务 5：SEO 公开化

- sitemap.py：`StaticViewSitemap` + 各内容库 Sitemap；`/sitemap.xml`、`/robots.txt`。
- 详情页 meta：`seo_extras` 模板标签或 base 区块，输出 description/canonical/OG。
- 404/500 错误页模板。
- 测试：`V40SeoTests`（sitemap 含已发布内容、robots 指向 sitemap、详情页 meta、错误页渲染）。

## 任务 6：文档同步 + 验收

- README / CHANGELOG / update_roadmap / deploy_linux 同步 v4.0。
- 验收：全量测试、check、makemigrations --check、collectstatic、git diff --check、提交推送。

---

## 规模预估

- 模型 1、迁移 1、服务 1、表单 1、模板 4-5、Admin 1、sitemap 1、测试类 5。
- 零新依赖（sitemaps 为 Django 内置）。
