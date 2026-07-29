# OrganicChemHub

OrganicChemHub 是一个面向本科有机化学学习和考研复习的人名反应与合成路线资料库。当前版本基于图片结构式展示，支持后台图片上传管理、前台搜索浏览和移动端适配。

部署文档：[docs/deploy_linux.md](docs/deploy_linux.md)  
更新规划：[docs/update_roadmap.md](docs/update_roadmap.md)

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py loaddata common_reactions
.\.venv\Scripts\python manage.py loaddata exam_reactions
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

如果默认包源无法安装 Django，可改用：

```powershell
.\.venv\Scripts\python -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

浏览器访问：

- 前台：http://127.0.0.1:8000/
- 后台：http://127.0.0.1:8000/admin/

## 宝塔面板部署

你的服务器部署目录建议使用：

```bash
/www/wwwroot/chem.wencker.top
```

完整步骤见：

```text
docs/deploy_baota_panel.md
```

部署模板文件：

- `deploy/chem.wencker.top.env.example`：服务器 `.env` 示例。
- `deploy/supervisor_organicchemhub.conf`：Supervisor 守护进程示例。
- `deploy/nginx_chem.wencker.top.conf`：Nginx 反向代理示例。

服务器同步 UI 或静态文件更新后，需要执行：

```bash
python manage.py migrate
python manage.py loaddata exam_reactions
python manage.py collectstatic --noinput
```

## 索引本地学习资料

```powershell
.\.venv\Scripts\python manage.py index_learning_resources "F:\2027考研资料\有机化学"
```

索引只保存文件标题、分类、年份、大小和本地路径等元信息，不会复制或公开文件内容。

## 测试

```powershell
.\.venv\Scripts\python manage.py test
.\.venv\Scripts\python manage.py check
```

## 内容维护建议

后台录入反应时，建议至少填写中文名、英文名、类型、简要说明、条件、考点和参考来源。结构式图片建议按照 [docs/image_production_guide.md](docs/image_production_guide.md) 的规范制作 SVG 上传。内容公开前将状态设为"已发布"；草稿和归档内容不会在前台展示。

---

## 版本历史

### 1.2 后台工具增强（2026-07-29）

- **CSV 导出**：Reaction、SyntheticRoute、LearningResource 三个列表页新增「导出选中为 CSV」操作，一键下载为 Excel 可打开的 UTF-8 CSV 文件。
- **内容质量仪表盘**：后台新增 `/admin/reactions/reaction/dashboard/` 页面，卡片展示总反应数、已发布/草稿/归档数、缺图片/摘要/条件/来源的反应数量，以及最近更新的反应列表。
- **CSV 导入补充字段**：`import_reactions_csv` 命令新增 `aliases`、`mechanism`、`scope`、`limitations` 字段覆盖。
- **测试全部通过**：44 项。

### 0.9 彻底移除 SMILES（2026-07-29）

- **数据库删除所有 SMILES 字段**：`Reaction.equation_smiles`、`SyntheticRoute.target_smiles`、`RouteStep.reactant_smiles`、`RouteStep.product_smiles` 全部移除。
- **后台完全改为图片上传**：删除旧版 `structure_image`/`structure_image_url` 折叠区，三个图片字段（反应方程式、反应机理、缩略图）各自独立分组，每个带预览 + 文件选择 + help_text 指引。
- **`get_equation_img_src()` 新增 fallback**：当 `equation_img` 为空时自动读取 `structure_image_url`，保证旧数据平滑过渡。
- **`get_thumbnail_img_src()` 新增 fallback**：缩略图为空时降级使用 `equation_img`。
- **清除所有 SMILES 代码引用**：views.py 删除 `target_smiles__icontains` 搜索字段，admin.py 删除 `search_fields` 中的 `target_smiles`，fixture 清理 SMILES 数据。
- **删除 backup_smiles 管理命令**（已完成历史使命）。
- **44 项测试全部通过**，代码零 SMILES 引用。

### 0.8 内容迁移（2026-07-29）

- 安装 RDKit 和 NumPy（`rdkit-pypi>=2022.9`、`numpy<2`、`Pillow>=10.0`），更新 requirements.txt。
- 编写 `scripts/generate_reaction_images.py`：批量解析非空 SMILES，使用 RDKit 生成 SVG 结构式图片。
- 生成 26 个反应的 equation SVG + thumbnail SVG（800×350 / 400×175 viewBox），存入 `static/images/reactions/`。
- 2 个 Wittig 反应因 SMILES 含非标准 `CPPh3` 缩写无法解析，手动从旧 PNG 迁移。
- 编写 `import_reaction_images` 管理命令：扫描命名文件 `reaction_{slug}_equation.svg`，自动匹配数据库记录并写入 `structure_image_url`。
- 18 个无 SMILES 的反应（Gabriel、Mannich、Sandmeyer 等）暂未生成图片，留待手动补全。
- 依赖新增：requirements.txt 添加 rdkit-pypi、Pillow、numpy<2。

### 0.7 前端展示改造（2026-07-29）

- 清理 base.html：确认无任何化学渲染库引用，仅保留 Bootstrap 5.3.3 CSS/JS 和 Bootstrap Icons，页脚版本号更新至 0.7。
- 清理死 CSS：删除 `.mini-smiles`、`.reaction-result-item__smiles`、`.structure-viewer__raw`、`.molecule-tile`、`.reaction-arrow` 及其所有子选择器，共减少约 100 行无用代码。
- 所有结构式图片增加 `onerror` 加载失败兜底：详情页显示"图片加载失败"文字提示，卡片和列表缩略图失败时自动隐藏。
- route_detail.html 完全移除 SMILES 条件判断和 `smiles=` 参数传递，只依靠图片字段决定是否展示。
- 移动端适配增强：`<576px` 时缩略图取消左侧间距，详情图 padding 收缩至 0.4rem，全部图片保持 `max-width: 100%`。
- 清理测试中无意义的渲染库断言。

### 0.6 后台与数据库改造（2026-07-29）

- Reaction 模型新增三个图片字段：`equation_img`（反应方程式）、`mechanism_img`（反应机理）、`thumbnail_img`（缩略图）。
- 上传自动重命名，按 `reaction_{slug}_{type}.{ext}` 格式存储到 `media/reaction_images/`。
- 后台管理界面重构：旧版 structure_image 字段折叠隐藏，新增分组图片上传控件和实时预览。
- 后台列表页增加缩略图列 `admin_thumbnail`。
- RouteStepInline 和 RouteStepAdmin 移除 SMILES 输入框。
- 前台模板移除 SMILES 文本展示，替换为缩略图和方程式图片。
- SMILES 数据保留在数据库（不删除、不迁移），仅在 UI 层隐藏，便于后续 RDKit 结构检索使用。
- 新增 SMILES 备份脚本 `backup_smiles`：`python manage.py backup_smiles` 导出 JSON。
- 备份文件保存至 `backups/smiles_backup_2026-07-29.json`。

### 0.5 图片规范与静态资源整理（2026-07-29）

- 制定图片文件命名规则，规范 Reaction、SyntheticRoute、RouteStep 三模型的 SVG 命名。
- 规划服务器图片存储目录结构：`static/images/reactions/`、`static/images/routes/`、`static/images/routes/steps/`。
- 确定图片统一规格（SVG 格式、Arial 字体、透明背景、键长/字号标准）。
- 选定 ChemDraw 为绘图工具，编写管理员图片制作规范文档。
- 旧 `static/img/reactions/lecture_*.png` 逐步迁移至新目录结构。

### 0.37 图片结构式与后台维护

- 结构式展示改为图片优先，不再依赖在线 SMILES 渲染。
- 反应、路线目标产物、路线步骤支持后台上传结构式图片或填写图片 URL。
- 后台增加结构式图片预览和配置状态。
- 从用户自制《有机化学复习讲义》中提取部分临时结构式图片。
- 保留 SMILES 文本作为排错和后续结构检索基础。

### 0.36 查询页与考研反应扩充

- 人名反应查询页改为左侧滚动目录、右侧结果内容区的资料库布局。
- 分页控件样式更新。
- 新增 exam_reactions fixture，补充 32 条考研常见人名反应。

### 0.35 UI 与结构式展示

- 前台首页、导航、卡片和详情页视觉升级。
- 反应详情页支持结构式展示（后续版本已迁移至纯图片方案）。
- 后台管理增加 OrganicChemHub 标题和基础主题样式。

### 0.3 搜索与分类增强

- 人名反应支持官能团筛选、考研高频快捷筛选。
- 反应、路线、学习资料列表支持排序。
- 搜索结果关键词高亮、空结果推荐、分页保留筛选条件。

### 0.25 首次部署与资料索引

- 首次部署引导页 `/deploy/`、宝塔面板部署文档。
- 常见人名反应 fixture（common_reactions）。
- 学习资料索引模型和页面、本地资料索引命令。

### 0.2 内容维护增强

- 发布前校验必填字段、后台列表显示内容完整度。
- 合成路线后台显示步骤数、批量发布/归档完整内容。

### 0.1 基础功能

- 人名反应模型、合成路线模型、路线步骤模型。
- Django Admin 后台增删改查。
- 首页、反应列表/详情、路线列表/详情。
- 公开页面只显示已发布内容、基础自动化测试。

---

## 后续版本方向

- RDKit 结构式 SVG 渲染与子结构检索。
- Ketcher 后台结构编辑器。
- 用户收藏和学习笔记。
- 批量导入导出。
