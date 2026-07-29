# OrganicChemHub v0.9 宝塔面板部署指南

> 目标服务器：**Debian 12** | **宝塔面板 10.0** | **LNMP 环境** | **域名 chem.wencker.top**
>
> 适用于全新部署，含 RDKit 图片生成和 Supervisor 守护进程配置。

---

## 目录

1. [上传代码](#1-上传代码)
2. [安装依赖与 RDKit](#2-安装依赖与-rdkit)
3. [配置环境变量](#3-配置环境变量)
4. [初始化数据库与导入数据](#4-初始化数据库与导入数据)
5. [生成结构式图片](#5-生成结构式图片)
6. [宝塔面板配置（Nginx + 反向代理）](#6-宝塔面板配置)
7. [Supervisor 守护进程](#7-supervisor-守护进程)
8. [申请 SSL 证书](#8-申请-ssl-证书)
9. [更新代码](#9-更新代码)
10. [RDKit 安装排错](#10-rdkit-安装排错)
11. [日常维护速查](#11-日常维护速查)

---

## 1. 上传代码

**方式 A — GitHub（推荐）**

```bash
cd /www/wwwroot
git clone 你的仓库地址 chem.wencker.top
```

**方式 B — 宝塔面板上传**

本地电脑把 `D:\code_files\OrganicChemHub_dsv0.9\` 打包为 zip，在宝塔「文件」上传到 `/www/wwwroot/` 并解压为 `chem.wencker.top`。

> 注意：上传后不需要 `.venv/`、`staticfiles/`、`media/` 目录，这些会在服务器上重新生成。

---

## 2. 安装依赖与 RDKit

```bash
cd /www/wwwroot/chem.wencker.top

# 创建 Python 虚拟环境
python3 -m venv .venv

# 激活虚拟环境（每步操作前都要执行这条）
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip

# ----- 安装 RDKit（关键：必须按顺序） -----
# 第1步：先装 numpy 1.x，RDKit 不兼容 numpy 2.x
pip install "numpy<2"

# 第2步：安装 RDKit（编译 C 扩展，约 1-3 分钟）
pip install rdkit-pypi

# 第3步：安装项目其他依赖
pip install -r requirements.txt

# 验证 RDKit
python -c "from rdkit import Chem; print('RDKit OK:', Chem.MolFromSmiles('CCO').GetNumAtoms(), 'atoms')"
```

**如果 pip 慢**，加清华镜像源：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "numpy<2"
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rdkit-pypi
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

---

## 3. 配置环境变量

```bash
cd /www/wwwroot/chem.wencker.top

# 复制环境变量模板
cp deploy/chem.wencker.top.env.example .env

# 生成随机 SECRET_KEY
python - <<'PY'
from pathlib import Path
from django.core.management.utils import get_random_secret_key
env = Path(".env")
text = env.read_text(encoding="utf-8")
text = text.replace("replace-this-with-a-long-random-secret-key", get_random_secret_key())
env.write_text(text, encoding="utf-8")
print("SECRET_KEY generated")
PY
```

> `.env` 文件包含生产环境配置（数据库密钥、域名白名单等），**不要提交到 Git**。

---

## 4. 初始化数据库与导入数据

```bash
# 先激活环境（如果不在虚拟环境中）
source .venv/bin/activate

# 创建数据库表
python manage.py migrate

# 导入反应数据
python manage.py loaddata common_reactions
python manage.py loaddata exam_reactions

# 在服务器创建管理员账号（按提示输入用户名、邮箱、密码）
python manage.py createsuperuser

# 收集静态文件（CSS、JS、图片 → 放到 Nginx 服务目录）
python manage.py collectstatic --noinput
```

---

## 5. 生成结构式图片

v0.9 使用 RDKit 读取数据库中的 SMILES 数据，批量生成 SVG 图片。

```bash
source .venv/bin/activate

# 用 RDKit 将 SMILES 渲染为 SVG（生成 ~52 个文件）
python scripts/generate_reaction_images.py

# 将 SVG 路径写入数据库
python manage.py import_reaction_images

# 收集到 Nginx 静态目录
python manage.py collectstatic --noinput
```

成功输出示例：

```
Found 28 reactions with SMILES.
[OK] reaction_friedel_crafts_acylation_equation.svg
[OK] reaction_common_aldol_reaction_equation.svg
...
Done: 26 OK, 2 FAIL
```

> 2 个 FAIL（Wittig 反应含非标准 SMILES），不影响运行，旧 PNG 图会自动兜底。

---

## 6. 宝塔面板配置

### 6.1 添加网站

宝塔 → 网站 → 添加站点：

| 字段 | 值 |
|------|-----|
| **域名** | `chem.wencker.top` |
| **根目录** | `/www/wwwroot/chem.wencker.top` |
| **PHP 版本** | 选「纯静态」 |

### 6.2 配置反向代理

宝塔 → 网站 → `chem.wencker.top` → 反向代理 → 添加反向代理：

| 字段 | 值 |
|------|-----|
| **目标 URL** | `http://127.0.0.1:8000` |
| **发送域名** | `$host` |

### 6.3 添加静态文件 Nginx 规则

宝塔 → 网站 → `chem.wencker.top` → **配置文件**。

找到 `#SSL-START` 上方，插入以下两段：

```nginx
    # ---------- 静态文件 ----------
    location /static/ {
        alias /www/wwwroot/chem.wencker.top/staticfiles/;
        expires 30d;
        access_log off;
    }

    location /media/ {
        alias /www/wwwroot/chem.wencker.top/media/;
        expires 7d;
    }
    # ------------------------------
```

点击「保存」，宝塔自动重载 Nginx。

**验证：** 浏览器访问以下链接应返回图片（不是 404）：

| 验证内容 | 地址 |
|---------|------|
| 生成的 SVG | `https://chem.wencker.top/static/images/reactions/reaction_common_aldol_reaction_equation.svg` |
| 旧 PNG 兜底 | `https://chem.wencker.top/static/img/reactions/lecture_wittig.png` |

---

## 7. Supervisor 守护进程

宝塔 → Supervisor 管理器 → 添加守护进程：

| 字段 | 值 |
|------|-----|
| **名称** | `organicchemhub` |
| **启动用户** | `www` |
| **运行目录** | `/www/wwwroot/chem.wencker.top` |
| **启动命令** | `/www/wwwroot/chem.wencker.top/.venv/bin/gunicorn organic_chem_hub.wsgi:application --chdir /www/wwwroot/chem.wencker.top --bind 127.0.0.1:8000 --workers 2 --timeout 60` |

其他字段保持默认，提交后点「启动」。

**检查是否正常运行：**

```bash
# 查看进程
ps aux | grep gunicorn

# 查看日志
tail -f /www/wwwlogs/organicchemhub.out.log
```

---

## 8. 申请 SSL 证书

宝塔 → 网站 → `chem.wencker.top` → **SSL** → Let's Encrypt → 申请免费证书。

申请完成后开启「强制 HTTPS」。

---

## 9. 更新代码

以后服务器上的代码需要更新时：

```bash
cd /www/wwwroot/chem.wencker.top

# 拉取最新代码
git pull

# 激活环境
source .venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 执行数据库迁移
python manage.py migrate

# 重新导入数据（如果有新反应）
python manage.py loaddata common_reactions
python manage.py loaddata exam_reactions

# 重新生成图片
python scripts/generate_reaction_images.py
python manage.py import_reaction_images

# 重新收集静态文件
python manage.py collectstatic --noinput
```

最后在宝塔 Supervisor 中重启 `organicchemhub`。

---

## 10. RDKit 安装排错

###  `_ARRAY_API not found`

numpy 版本冲突，RDKit 必须用 numpy 1.x。

```bash
source .venv/bin/activate
pip install "numpy<2"
python -c "import numpy; print(numpy.__version__)"   # 必须显示 1.x
```

### `libOpenGL.so.0: cannot open shared object file`

Debian 12 最小安装缺 OpenGL 库。

```bash
apt-get install -y libgl1-mesa-glx libglib2.0-0
pip install --force-reinstall rdkit-pypi
```

### `No module named 'rdkit'`

RDKit 没有装到当前虚拟环境里。

```bash
# 检查当前 python 路径
which python       # 应显示 .venv/bin/python
# 检查已安装包
pip list | grep rdkit
# 如未安装：
pip install rdkit-pypi
```

---

## 11. 日常维护速查

| 操作 | 方法 |
|------|------|
| 启动/重启服务 | 宝塔 → Supervisor → 重启 `organicchemhub` |
| 查看运行日志 | `tail -f /www/wwwlogs/organicchemhub.out.log` |
| 查看错误日志 | `tail -f /www/wwwlogs/organicchemhub.err.log` |
| 更新代码 | `git pull && source .venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && 重启 Supervisor` |
| 重新生成图片 | `source .venv/bin/activate && python scripts/generate_reaction_images.py && python manage.py import_reaction_images && python manage.py collectstatic --noinput` |
| 备份数据库 | `cp /www/wwwroot/chem.wencker.top/db.sqlite3 /备份目录/db.$(date +%Y%m%d).sqlite3` |

---

## 附录：最终服务器目录结构

```
/www/wwwroot/chem.wencker.top/
├── .env                         # 生产环境配置
├── db.sqlite3                   # SQLite 数据库
├── .venv/                       # Python 虚拟环境
├── static/
│   └── images/reactions/        # 生成的 SVG 结构式图片
│       ├── reaction_common_aldol_reaction_equation.svg
│       └── ...
├── staticfiles/                 # Nginx 直接服务的静态文件
├── media/                       # 后台上传的图片
├── scripts/
│   └── generate_reaction_images.py   # SMILES → SVG 生成脚本
└── docs/deploy_linux.md         # 本指南
```
