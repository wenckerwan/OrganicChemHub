# OrganicChemHub

OrganicChemHub 是一个面向本科有机化学学习和考研复习的有机反应资料库。项目采用 Django Admin 作为标准内容管理层，前台负责清晰展示人名反应、常见有机反应、合成路线、学习资料、公告和用户互动数据。

当前版本：**v2.3**

部署文档：[docs/deploy_linux.md](docs/deploy_linux.md)
更新日志：[docs/CHANGELOG.md](docs/CHANGELOG.md)
后续规划：[docs/organic_chem_hub_update_roadmap.md](docs/organic_chem_hub_update_roadmap.md)

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
- 路线列表/详情：目标产物图片、步骤时间线、反应物/产物图片。
- 访问统计：首页展示网站总访问量和今日访问量，反应/路线详情页展示本页总访问量和今日访问量。
- 用户中心：收藏、笔记、学习进度、反馈记录和站内消息。

### 后台管理
- Django Admin 维护人名反应、常见有机反应、合成路线、分类、标签、官能团、公告、反馈和站内消息。
- 列表页支持搜索、筛选、排序、缩略图预览、完整度展示和批量发布/归档。
- 内容质量仪表盘：`/admin/reactions/dashboard/`。
- CSV 导入入口：`/admin/reactions/import/`，支持人名反应和常见有机反应。
- 图片维护入口：`/admin/reactions/images/`，集中查看缺方程式图、缺缩略图和缺机理图内容。
- 消息群发与消息清理：运营人员可通过专用后台工具完成站内通知维护。
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

后续每次功能更新、修复或数据导入都需要同步更新根目录 `README.md`，至少补充“当前版本”和“版本历史”中的核心内容。

提交信息统一使用中文版本号格式：

```bash
git commit -m "v2.1: 内容发布完善 - 前台状态与自动发布工具"
```

不再使用 `fix: ...`、`feat: ...` 这类英文 Conventional Commit 格式。

---

## 版本历史

| 版本 | 日期 | 核心内容 |
|------|------|---------|
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
