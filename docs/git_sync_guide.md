# OrganicChemHub Git 同步完整指南

---

## 一、初始化 Git 仓库（第一次做）

### 在本地电脑 PowerShell

```powershell
cd D:\code_files\OrganicChemHub_dsv0.9

# 初始化 Git 仓库
git init

# 添加所有文件到暂存区
git add .

# 首次提交
git commit -m "v0.9 初始化：纯图片结构式版本"

# 关联远程仓库（如果没有，先去 GitHub 新建一个空白仓库）
git remote add origin https://github.com/你的用户名/OrganicChemHub.git

# 推送到 GitHub
git push -u origin master
```

> 注意：`.gitignore` 已经排除了 `.venv/`、`db.sqlite3`、`media/`、`staticfiles/`、`.env`，这些不会上传。

---

## 二、服务器首次部署（第一次做）

### 在 Xshell

```bash
cd /www/wwwroot

# 从 GitHub 克隆代码
git clone https://github.com/你的用户名/OrganicChemHub.git chem.wencker.top

cd chem.wencker.top

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "numpy<2"
pip install rdkit-pypi
pip install -r requirements.txt

# 配置环境变量
cp deploy/chem.wencker.top.env.example .env
python -c "from pathlib import Path; from django.core.management.utils import get_random_secret_key; p=Path('.env'); t=p.read_text(); p.write_text(t.replace('replace-this-with-a-long-random-secret-key', get_random_secret_key()))"

# 初始化数据库
python manage.py migrate
python manage.py loaddata common_reactions
python manage.py loaddata exam_reactions
python manage.py createsuperuser

# 生成图片
python scripts/generate_reaction_images.py
python manage.py import_reaction_images

# 收集静态文件
python manage.py collectstatic --noinput
```

---

## 三、日常同步流程

### 场景 1：本地改了代码，同步到服务器

```mermaid
本地电脑             →  GitHub            →  服务器
 写代码                git push              git pull
 跑测试                                     重启 Supervisor
```

**本地 PowerShell：**

```powershell
cd D:\code_files\OrganicChemHub_dsv0.9

# 查看改了哪些文件
git status

# 添加并提交
git add .
git commit -m "v1.0: 添加xxx功能"

# 推送到 GitHub
git push
```

**服务器 Xshell：**

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate

# 拉取最新代码
git pull

# 如果有新依赖
pip install -r requirements.txt

# 如果数据库模型有变化
python manage.py migrate

# 重新收集静态文件
python manage.py collectstatic --noinput

# 重启服务
supervisorctl restart organicchemhub
```

---

### 场景 2：服务器后台添加了反应，同步到本地开发

```mermaid
服务器              →  本地电脑
 导出数据库            覆盖本地 db.sqlite3
 下载 media/           覆盖本地 media/
```

**服务器 Xshell：**

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate

# 导出最新数据为 JSON（可选，此文件可以下载到本地）
python manage.py dumpdata reactions > data_backup.json

# 查看数据库文件位置
ls -lh db.sqlite3
ls -lh media/reaction_images/
```

**本地 PowerShell（用宝塔面板的文件功能下载）：**

```
宝塔 → 文件 → /www/wwwroot/chem.wencker.top/
  ├── db.sqlite3         → 下载 → 覆盖本地 D:\code_files\OrganicChemHub_dsv0.9\db.sqlite3
  └── media/             → 下载 → 覆盖本地 D:\code_files\OrganicChemHub_dsv0.9\media/
```

或者用 `scp` 命令直接从服务器拉（Xshell）：

```bash
# 在本地 PowerShell 执行（不是服务器）
scp root@服务器IP:/www/wwwroot/chem.wencker.top/db.sqlite3 D:\code_files\OrganicChemHub_dsv0.9\
scp -r root@服务器IP:/www/wwwroot/chem.wencker.top/media/ D:\code_files\OrganicChemHub_dsv0.9\media\
```

---

### 场景 3：本地新增反应 + 代码改动，一起推送到服务器

```mermaid
本地电脑             →  GitHub            →  服务器
 数据库已更新            git push             git pull
 代码已更新              （代码+fixture）      重新加载数据
```

**本地 PowerShell：**

```powershell
cd D:\code_files\OrganicChemHub_dsv0.9

# 把本地数据库的最新反应数据导出为 fixture（这样服务器也能加载）
.venv\Scripts\python manage.py dumpdata reactions --indent 2 > reactions/fixtures/v1_0_full.json

# 提交代码 + 新数据
git add .
git commit -m "v1.0: 补全 18 条缺图反应"
git push
```

**服务器 Xshell：**

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate

# 拉取代码 + fixture
git pull

# 加载新数据（--ignorenonexistent 避免旧 fixture 报错）
python manage.py loaddata reactions/fixtures/v1_0_full.json --ignorenonexistent

# 运行 migrate（如果有模型变化）
python manage.py migrate

# 重新收集静态文件
python manage.py collectstatic --noinput

# 重启
supervisorctl restart organicchemhub
```

---

## 四、.gitignore 确认（你的数据安全）

当前项目的 `.gitignore`：

```
.venv/          # 虚拟环境（不提交）
__pycache__/    # Python 缓存（不提交）
*.py[cod]       # 编译文件（不提交）
*.sqlite3       # 所有数据库（不提交）
db.sqlite3      # 主数据库（不提交）
.env            # 环境变量（不提交）
.pytest_cache/  # 测试缓存（不提交）
.coverage       # 覆盖率报告（不提交）
htmlcov/        # 覆盖率页面（不提交）
staticfiles/    # 收集后的静态文件（不提交）
media/          # 用户上传图片（不提交）
backups/        # 备份文件（不提交）
```

**你手动添加的反应数据在 `db.sqlite3` 和 `media/` 里 → 不会被 Git 提交 → 永远安全。**

---

## 五、更新版本的标准操作

以后你发布了 v1.1、v1.2 等新版本，流程永远是：

```mermaid
flowchart LR
    A[本地开发]
    A --> B[git add .]
    B --> C[git commit -m "版本号"]
    C --> D[git push]
    D --> E[服务器 git pull]
    E --> F[pip install -r requirements.txt]
    F --> G[python manage.py migrate]
    G --> H[python manage.py collectstatic]
    H --> I[supervisorctl restart]
```

**你的数据（自己添加的反应、上传的图片）全程不受影响。**
