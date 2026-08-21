# OrganicChemHub

OrganicChemHub 是一个面向本科有机化学学习和考研复习的有机反应资料库。项目采用 Django Admin 作为标准内容管理层，前台负责清晰展示人名反应、常见有机反应、合成路线、学习资料、公告和用户互动数据。

当前版本：**v4.0 已交付**
下个版本：**待定**

部署文档：[docs/deploy_linux.md](docs/deploy_linux.md)
更新日志：[docs/CHANGELOG.md](docs/CHANGELOG.md)
后续规划：[docs/organic_chem_hub_update_roadmap.md](docs/organic_chem_hub_update_roadmap.md)

开发文档索引：

- v4.0 设计规格：[docs/superpowers/specs/2026-08-21-v40-comments-and-public-design.md](docs/superpowers/specs/2026-08-21-v40-comments-and-public-design.md)
- v4.0 实施计划：[docs/superpowers/plans/2026-08-21-v40-comments-and-public-implementation.md](docs/superpowers/plans/2026-08-21-v40-comments-and-public-implementation.md)
- v3.0 设计规格：[docs/superpowers/specs/2026-08-20-v30-public-stable-design.md](docs/superpowers/specs/2026-08-20-v30-public-stable-design.md)
- v3.0 实施计划：[docs/superpowers/plans/2026-08-20-v30-public-stable-implementation.md](docs/superpowers/plans/2026-08-20-v30-public-stable-implementation.md)
- v2.8 设计规格：[docs/superpowers/specs/2026-08-20-v28-ops-audit-design.md](docs/superpowers/specs/2026-08-20-v28-ops-audit-design.md)
- v2.8 实施计划：[docs/superpowers/plans/2026-08-20-v28-ops-audit-implementation.md](docs/superpowers/plans/2026-08-20-v28-ops-audit-implementation.md)
- v2.7 设计规格：[docs/superpowers/specs/2026-08-20-v27-routes-expansion-design.md](docs/superpowers/specs/2026-08-20-v27-routes-expansion-design.md)
- v2.7 实施计划：[docs/superpowers/plans/2026-08-20-v27-routes-expansion-implementation.md](docs/superpowers/plans/2026-08-20-v27-routes-expansion-implementation.md)
- v2.6 设计规格：[docs/superpowers/specs/2026-08-20-v26-study-progress-design.md](docs/superpowers/specs/2026-08-20-v26-study-progress-design.md)
- v2.6 实施计划：[docs/superpowers/plans/2026-08-20-v26-study-progress-implementation.md](docs/superpowers/plans/2026-08-20-v26-study-progress-implementation.md)
- v2.5 设计规格：[docs/superpowers/specs/2026-08-13-v25-study-topics-design.md](docs/superpowers/specs/2026-08-13-v25-study-topics-design.md)
- v2.5 实施计划：[docs/superpowers/plans/2026-08-13-v25-study-topics-implementation.md](docs/superpowers/plans/2026-08-13-v25-study-topics-implementation.md)

项目目录约定：业务代码位于 `organic_chem_hub/`、`reactions/`；前台模板和静态资源分别位于 `templates/`、`static/`；部署配置位于 `deploy/`；项目文档位于 `docs/`；本地资料和反应图片素材位于 `data/`，不上传服务器。

---

## 功能概览

### 内容管理
- 人名反应：中文名、英文名、分类、标签、官能团、摘要、条件、机理、考点、适用范围、限制、参考来源、状态。
- 常见有机反应：与人名反应分库管理，前台使用独立入口、标题和视觉主题。
- 合成路线：目标产物、摘要、难度、优缺点、来源、关联反应和路线步骤。
- 图片字段：方程式图、机理图、缩略图均支持后台上传；机理图可选，方程式图和缩略图计入发布质量检查。
- 学习资料：标题、分类、年份、文件类型、文件来源、是否含答案、状态。

### 前台页面
- 首页：公告栏、搜索栏、快速入口、前台内容状态、最近更新反应、合成路线、分类标签和反馈表单。
- 首页“进入后台维护”按钮仅管理员可见，未登录用户和普通用户隐藏。
- 人名反应库：独立蓝色主题，展示已发布人名反应。
- 常见有机反应库：独立青绿色主题，展示已发布常见反应。
- 反应详情：结构式图片、摘要、条件、机理、考点、收藏、学习进度和私人笔记。
- 考研专题：专题列表/详情页，按知识模块组织已发布反应和路线；专题详情展示个人学习进度条，可内联切换学习状态；易混反应对比并列展示两个反应。
- 个人中心：收藏、笔记、学习进度、专题完成度、复习清单、最近学习记录、反馈和站内消息。
- 路线列表/详情：目标产物图片、步骤时间线、反应物/产物图片；支持按难度、目标官能团筛选与排序，关键步骤高亮展示。
- 访问统计：首页展示网站总访问量和今日访问量，反应/路线详情页展示本页总访问量和今日访问量。

### 后台管理
- Django Admin 维护人名反应、常见有机反应、合成路线、分类、标签、官能团、公告、反馈和站内消息。
- 列表页支持搜索、筛选、排序、缩略图预览、完整度展示和批量发布/归档。
- 内容质量仪表盘：`/admin/reactions/dashboard/`。
- CSV 导入入口：`/admin/reactions/import/`，支持人名反应和常见有机反应，导入错误可下载 CSV 修复后重导。
- 图片维护入口：`/admin/reactions/images/`，集中查看缺方程式图、缺缩略图和缺机理图内容。
- 消息群发与消息清理：运营人员可通过专用后台工具完成站内通知维护。
- 内容批次记录与操作日志：批量发布/归档、CSV 导入、消息清理自动记录批次与审计日志，后台可筛选追踪。
- 访问统计：后台可只读查看网站、反应和合成路线访问量。

### v2.1 新增
- 首页增加“前台内容状态”，展示已发布人名反应、常见有机反应、合成路线和待发布完整内容数量。
- 内容质量仪表盘增加“可发布草稿”计数，帮助管理员快速找到已经补全但尚未发布的内容。
- 新增 `publish_ready_content` 管理命令，只发布字段完整的草稿，缺图或缺关键字段的内容保持草稿。
- 运行依赖回归轻量化，结构式展示以后台上传图片为准。

### v2.2 新增
- 反应附图支持多图上传：方程式图、机理图、反应条件附图、机理文字附图、考点附图，每个区域最多 10 张。
- 条件、机理文字和考点附图均为可选，不影响发布。
- 多张方程式图可满足“反应方程式图”发布完整度检查。
- 前台详情页按区域展示多图附图，后台反应编辑页提供内联上传。

### v2.3 新增
- 新增网站访问统计，首页展示网站总访问量和今日访问量。
- 新增内容访问统计，人名反应、常见有机反应和合成路线详情页展示本页总访问量和今日访问量。
- 访问统计样式复用前台状态卡片风格，保持首页和详情页视觉一致。
- 后台新增“访问统计”只读列表，便于管理员核对数据。

### v2.4 新增
- 内容质量仪表盘增加图片审核状态、缺失项统计和“高访问但未完整”优先补全列表。
- 反应附图支持“待审核 / 已通过 / 需重画”状态，并支持后台批量审核。
- 人名反应和常见反应后台列表展示总访问量、今日访问量。

### v4.0 已交付（2026-08-21）
- 评论/社区：新增 `Comment` 模型（GFK 通用内容关联，复用收藏/笔记模式），详情页评论区支持登录评论与回复，匿名显示登录引导；后台审核隐藏（写 OpLog）；个人中心新增"我的评论"。
- SEO 公开化：sitemap.xml（全部已发布内容）+ robots.txt；详情页独立 meta description / canonical / OG 标签；404/500 友好错误页。
- 零新依赖（sitemaps 为 Django 内置）。

### v3.0 已交付
- 占位图工作流：新增 `reactions/services/placeholder.py`，为缺图反应一键生成中性占位图（方程图 + 缩略图），让内容通过发布校验并上线，待替换真图。
- 图片维护工具增强：按缺失类型筛选（方程图/缩略图/机理图）、全量分页展示、批量生成占位图（写入 OpLog + ContentBatch）。
- 内容就绪报告：新增 `content_readiness_report` 管理命令与 `reactions/services/readiness.py`，输出各库就绪度统计与逐条缺失清单 CSV（`--export`）。
- 发布流程闭环：`publish_ready_content` 发布后写入操作日志与内容批次；仪表盘增加占位图待替换计数。
- 零模型变更、零迁移。

### v2.8 已交付
- 内容批次记录：新增 `ContentBatch` 模型，批量发布/归档、CSV 导入、消息清理自动记录批次（类型/操作人/数量/对象摘要）。
- 操作日志覆盖增强：新增 `reactions/services/audit.py` 统一写入入口；批量发布/归档与 CSV 导入均写入 OpLog；后台日志按操作筛选。
- 导入错误报告下载：CSV 导入错误结构化（行号/字段/原始值/建议修复），支持下载 CSV 修复后重新导入。
- 备份与恢复文档：部署文档新增数据库备份、media 备份、git 回滚流程。

### v2.7 已交付
- 目标官能团筛选：路线列表支持按目标官能团筛选（与难度/搜索/排序叠加），详情页展示官能团徽标并可回跳列表。
- 关键步骤标记：路线步骤支持标记"关键步骤"，详情页时间线高亮展示，后台可维护。
- 后台步骤编辑增强：内联步骤支持图片缩略图预览、关键步骤编辑；步骤序号校验从 1 连续无缺号；列表显示关键步骤数与缺图提醒。
- 模型变更：`RouteStep.is_key_step`、`SyntheticRoute.related_functional_groups`（复用现有官能团模型）。

### v2.6 新增
- 专题进度：专题详情页展示"我的专题进度"进度条（已学/总数），反应和路线卡片显示学习状态徽标，支持专题内直接切换状态。
- 复习清单：个人中心集中展示全部待复习内容，按最近标记时间排序。
- 最近学习记录：个人中心按时间倒序展示最近学习动态。
- 个人中心新增专题进度聚合列表，按专题查看完成度。
- 不新增数据模型，新增 `reactions/services/progress.py` 服务层集中统计。

### v2.5 新增
- 新增考研专题学习：专题分类、学习目标、考试重点、关联反应和合成路线。
- 新增易混反应对比：适用底物、反应条件、主要产物、常见考法和易错点。
- 首页新增专题学习和易混反应对比入口。
- 个人中心新增待学习、待复习和已学内容复习入口。
- 专题详情页和易混反应对比详情页接入访问统计。
- 用户互动（收藏、笔记、学习进度）改用通用内容关联，同时支持人名反应、常见有机反应和旧版反应。

目录整理已完成：本地反应图片素材已归档到 `data/reaction_image_library/`，源资料已归档到 `data/source/`；两者均不提交 Git、不上传服务器。

---

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py setup_admin_roles
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

浏览器访问：

- 前台：http://127.0.0.1:8000/
- 后台：http://127.0.0.1:8000/admin/

---

## 常用维护命令

```powershell
# 检查项目配置
.\.venv\Scripts\python manage.py check

# 发布字段完整的反应草稿
.\.venv\Scripts\python manage.py publish_ready_content

# 只预览可发布数量，不写入数据库
.\.venv\Scripts\python manage.py publish_ready_content --dry-run

# 初始化后台角色
.\.venv\Scripts\python manage.py setup_admin_roles

# 运行测试
.\.venv\Scripts\python manage.py test
```

服务器同步更新：

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
git pull origin master
pip install -r requirements.txt
rm -f reactions/migrations/0012_alter_learningresource_local_path.py
rm -f reactions/migrations/0014_merge_20260730_1535.py
rm -f reactions/migrations/0016_merge_20260802_2239.py
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_admin_roles
/www/server/panel/pyenv/bin/supervisorctl restart all
```

---

## 图片制作规范

反应结构式图片按照 [docs/image_production_guide.md](docs/image_production_guide.md) 的规范制作后上传。建议使用 SVG，透明背景，线条清晰，适合在列表页和详情页同时展示。

图片自动重命名规则：`media/reaction_images/reaction_{slug}_{type}.{ext}`。

---

## Git 同步规范

后续每次功能更新、修复、数据导入、开发文档、设计规格或实施计划，都必须保存到项目目录，并同步更新根目录 `README.md`。

文档更新要求：

- 设计规格保存到 `docs/superpowers/specs/`。
- 实施计划保存到 `docs/superpowers/plans/`。
- 版本说明和变更记录保存到 `docs/CHANGELOG.md`。
- 部署、开发和维护说明保存到 `docs/` 对应文档。
- README 至少同步当前版本、文档入口和版本历史。
- 文档与代码变更一起提交 Git，不单独留在聊天记录中。

提交信息统一使用中文版本号格式：

```bash
git commit -m "v2.1: 内容发布完善 - 前台状态与自动发布工具"
```

不再使用 `fix: ...`、`feat: ...` 这类英文 Conventional Commit 格式。

---

## 版本历史

| 版本 | 日期 | 核心内容 |
|------|------|---------|
| v3.0 | 2026-08-20 | 公开稳定版：占位图工作流、图片维护增强、内容就绪报告、发布流程闭环（已完成） |
| v4.0 | 2026-08-21 | 评论与公开化：评论/回复/审核、SEO sitemap/meta、错误页（已完成） |
| v2.8 | 2026-08-20 | 运营与审计：内容批次记录、操作日志覆盖、导入错误报告下载、备份恢复文档（已完成） |
| v2.7 | 2026-08-20 | 合成路线扩充：目标官能团筛选、关键步骤标记、后台步骤编辑增强（已完成） |
| v2.6 | 2026-08-20 | 学习进度与复习系统：专题进度、复习清单、最近学习记录（已完成） |
| v2.5 | 2026-08-20 | 考研专题学习：专题分类、易混反应对比与复习入口（已完成）；用户互动支持新反应库 |
| v2.4 | 2026-08-03 | 内容质量增强：图片审核状态、质量仪表盘、高访问不完整内容、反应列表访问量 |
| v2.3 | 2026-08-03 | 访问统计：网站总访问量/今日访问量，反应与合成路线详情页本页访问量，后台只读统计 |
| v2.2 | 2026-08-03 | 反应多图上传：方程式图、机理图、条件附图、机理文字附图、考点附图均支持每区最多 10 张 |
| v2.1 | 2026-08-03 | 内容发布完善：前台内容状态、后台可发布草稿统计、完整草稿自动发布命令、清理旧结构式生成依赖 |
| v2.0 | 2026-08-03 | 后台内容管理正式版：人名反应/常见有机反应分库、后台工具 UI、内容质量仪表盘、CSV 导入、图片维护、运营消息工具 |
| v1.6 | 2026-08-03 | 前台反应库 UI 与导航分流：人名反应库和常见有机反应库使用独立标题、入口和主题 |
| v1.5 | 2026-07-29 | 反馈升级与站内消息系统 |
| v1.4 | 2026-07-29 | 用户体系：注册、登录、收藏、私人笔记、学习进度、个人中心 |
| v1.3 | 2026-07-29 | 公告、弹窗、置顶、显示时段和意见反馈 |
| v1.2 | 2026-07-29 | CSV 导出、内容质量仪表盘和导入字段补充 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 / Django 5.2 LTS |
| 数据库 | SQLite（开发与当前生产）/ 后续可迁移 PostgreSQL |
| 前端 | Bootstrap 5.3.3 / Bootstrap Icons |
| 图片制作 | ChemDraw 或其他结构式绘图工具导出 SVG/PNG |
| 服务器 | Gunicorn / Nginx / Supervisor |
| 部署 | 宝塔面板 / Debian / Git + GitHub |

---

## 当前开发原则

- 前台只展示已发布内容，草稿和归档内容不公开。
- 结构式展示采用图片上传与审核，不再回到文本结构式生成路线。
- 人名反应和常见有机反应保持分库管理、分入口展示。
- 后台优先服务内容录入、质量检查、批量维护和运营处理。

## 本地资料目录

- `data/source/`：数据库建设指引和考研反应整理等本地源资料。
- `data/reaction_image_library/`：人工整理的反应图片素材库，按反应或专题分目录保存。
- `.superpowers/`：本地开发过程记录，不参与项目运行，也不提交 Git。
- `staticfiles/`、`.venv/`、`db.sqlite3`、`backups/`：本地运行或备份目录，不提交 Git。
