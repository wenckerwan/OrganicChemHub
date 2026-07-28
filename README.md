# OrganicChemHub

OrganicChemHub 是一个面向本科有机化学学习和考研复习的人名反应与合成路线资料库。0.1 版本聚焦基础功能：后台维护、公开搜索、反应详情、路线详情。

## 0.1 功能

- 人名反应模型：类型、标签、官能团、SMILES、条件、机理、考点、参考来源。
- 合成路线模型：目标产物、路线摘要、优缺点、难度、相关反应。
- 路线步骤模型：按步骤维护试剂、条件、产物、产率和关联反应。
- Django Admin 后台增删改查。
- 首页、反应列表、反应详情、路线列表、路线详情。
- 公开页面只显示已发布内容。
- 基础自动化测试。

## 0.2 内容维护增强

- 已发布反应必须填写摘要、反应条件和参考来源。
- 已发布路线必须填写目标产物、路线摘要，并至少包含一个路线步骤。
- 后台列表显示内容完整度。
- 合成路线后台列表显示步骤数。
- 后台支持批量发布完整内容。
- 后台支持批量归档内容。

## 0.25 首次部署与资料索引

- 新增首次部署引导页：`/deploy/`。
- 新增宝塔面板部署文档：`docs/deploy_baota_panel.md`。
- 新增常见人名反应 fixture：`common_reactions`。
- 新增学习资料索引模型和页面：`/learning-resources/`。
- 新增本地资料索引命令：`index_learning_resources`。

## 0.3 搜索与分类增强

- 人名反应支持官能团筛选。
- 人名反应支持“只看考研高频”快捷筛选。
- 反应、路线、学习资料列表支持排序。
- 搜索结果中关键词高亮显示。
- 空结果页面显示推荐内容。
- 分页链接保留当前搜索和筛选条件。

## 0.35 UI 与结构式展示

- 前台首页、导航、卡片和详情页视觉升级。
- 反应详情页支持将反应 SMILES 前端渲染为结构式。
- 合成路线详情页支持目标产物和步骤产物结构式展示。
- 保留原始 SMILES，便于复制和检查。
- 后台管理增加 OrganicChemHub 标题和基础主题样式。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py loaddata sample_data
.\.venv\Scripts\python manage.py loaddata common_reactions
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

后台录入反应时，建议至少填写中文名、英文名、类型、简要说明、条件、考点和参考来源。内容公开前将状态设为“已发布”；草稿和归档内容不会在前台展示。

## 后续版本方向

- RDKit 结构式 SVG 渲染。
- Ketcher 后台结构编辑器。
- 子结构检索。
- 用户收藏和学习笔记。
- 批量导入导出。
