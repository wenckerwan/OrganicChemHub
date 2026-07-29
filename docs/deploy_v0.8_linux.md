# OrganicChemHub v0.8 服务器部署指南

> 目标服务器：Debian 12 | 宝塔面板 10.0 | LNMP | 域名 chem.wencker.top

---

## 一、首次部署（从零开始）

### 1. 上传代码

**方式 A — 通过 GitHub（推荐）**

```bash
cd /www/wwwroot
git clone 你的仓库地址 chem.wencker.top
```

**方式 B — 通过宝塔面板**

在宝塔面板「文件」页面上传压缩包，解压到 `/www/wwwroot/chem.wencker.top/`。

### 2. 创建虚拟环境并安装依赖（含 RDKit）

Debian 12 自带 Python 3.11，可以直接用系统 Python。

```bash
cd /www/wwwroot/chem.wencker.top

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip 本身（重要，旧版 pip 安装 RDKit 可能失败）
pip install --upgrade pip

# 先装 numpy 1.x（核心！RDKit 不兼容 numpy 2.x）
pip install "numpy<2"

# 再装 RDKit（会自动拉 Pillow 等依赖，编译约 1-3 分钟）
pip install rdkit-pypi

# 如果编译报错，先装编译工具再重试：
# apt-get install -y build-essential cmake libgl1-mesa-glx libglib2.0-0
# pip install --force-reinstall rdkit-pypi

# 最后装项目其他依赖
pip install -r requirements.txt

# 验证 RDKit 安装成功
python -c "from rdkit import Chem; print('RDKit OK:', Chem.MolFromSmiles('CCO').GetNumAtoms(), 'atoms')"
```

**如果 pip 安装慢**，加清华源：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "numpy<2"
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rdkit-pypi
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 3. 配置环境变量

```bash
cp deploy/chem.wencker.top.env.example .env
```

生成随机 `SECRET_KEY`：

```bash
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

### 4. 初始化数据库

```bash
# 创建数据库表
python manage.py migrate

# 导入反应数据
python manage.py loaddata common_reactions
python manage.py loaddata exam_reactions

# 收集静态文件（CSS、图片等）
python manage.py collectstatic --noinput

# 创建管理员账号
python manage.py createsuperuser
```

### 5. 批量生成结构式图片（v0.8 新增步骤）

```bash
source .venv/bin/activate

# 用 RDKit 将 SMILES 自动渲染为 SVG
python scripts/generate_reaction_images.py

# 将生成的 SVG 路径写入数据库
python manage.py import_reaction_images

# 将 SVG 收集到 Nginx 服务的静态目录
python manage.py collectstatic --noinput
```

查看 `generate_reaction_images.py` 的输出，应该看到：

```
Found 28 reactions with SMILES.
[OK] reaction_friedel_crafts_acylation_equation.svg
[OK] reaction_common_aldol_reaction_equation.svg
...
Done: 26 OK, 2 FAIL
```

2 个 FAIL 是 Wittig 反应的 `CPPh3`（非标准 SMILES 缩写），不影响，它们会走旧 PNG 兜底。

### 6. 临时启动测试

```bash
source .venv/bin/activate
gunicorn organic_chem_hub.wsgi:application --chdir /www/wwwroot/chem.wencker.top --bind 127.0.0.1:8000 --workers 2
```

浏览器访问 `http://服务器公网IP:8000` 确认页面能正常打开。确认后 `Ctrl+C` 停止。

---

## 二、宝塔面板配置

### 1. 添加网站

宝塔 → 网站 → 添加站点：

| 字段 | 值 |
|------|-----|
| 域名 | `chem.wencker.top` |
| 根目录 | `/www/wwwroot/chem.wencker.top` |
| PHP 版本 | 纯 Python 项目，选「纯静态」 |

### 2. 配置反向代理

宝塔 → 网站 → `chem.wencker.top` → 反向代理 → 添加反向代理：

| 字段 | 值 |
|------|-----|
| 目标 URL | `http://127.0.0.1:8000` |
| 发送域名 | `$host` |

### 3. 添加静态文件 Nginx 规则

宝塔 → 网站 → `chem.wencker.top` → 配置文件，在 `server` 块内添加：

```nginx
server
{
    listen 80;
    server_name chem.wencker.top;
    index index.php index.html index.htm default.php default.htm default.html;
    root /www/wwwroot/chem.wencker.top;
    include /www/server/panel/vhost/nginx/extension/chem.wencker.top/*.conf;
    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/chem.wencker.top.conf;
    #CERT-APPLY-CHECK--END

    # ---------- 静态文件（在这加！） ----------
    location /static/ {
        alias /www/wwwroot/chem.wencker.top/staticfiles/;
        expires 30d;
        access_log off;
    }

    location /media/ {
        alias /www/wwwroot/chem.wencker.top/media/;
        expires 7d;
    }
    # -----------------------------------------

    #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  错误页配置，可以注释、删除或修改
    error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END

    #PHP-INFO-START  PHP引用配置，可以注释或修改
    #清理缓存规则

    location ~ /purge(/.*) {
        proxy_cache_purge cache_one $host$1$is_args$args;
        #access_log  /www/wwwlogs/chem.wencker.top_purge_cache.log;
    }
	#引用反向代理规则，注释后配置的反向代理将无效
	include /www/server/panel/vhost/nginx/proxy/chem.wencker.top/*.conf;

	include enable-php-00.conf;
    #PHP-INFO-END

    #REWRITE-START URL重写规则引用,修改后将导致面板设置的伪静态规则失效
    include /www/server/panel/vhost/rewrite/chem.wencker.top.conf;
    #REWRITE-END

    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }

    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {
        return 403;
    }

    

    
    access_log  /www/wwwlogs/chem.wencker.top.log;
    error_log  /www/wwwlogs/chem.wencker.top.error.log;
}
```

### 4. 配置 Supervisor（长期运行）

宝塔 → Supervisor 管理器 → 添加守护进程：

| 字段 | 值 |
|------|-----|
| 名称 | `organicchemhub` |
| 运行目录 | `/www/wwwroot/chem.wencker.top` |
| 启动用户 | `www` |
| 启动命令 | `/www/wwwroot/chem.wencker.top/.venv/bin/gunicorn organic_chem_hub.wsgi:application --chdir /www/wwwroot/chem.wencker.top --bind 127.0.0.1:8000 --workers 2 --timeout 60` |

### 5. 申请 SSL 证书

宝塔 → 网站 → `chem.wencker.top` → SSL → 申请 Let's Encrypt 免费证书，开启强制 HTTPS。

---

## 三、更新代码（已有部署）

```bash
cd /www/wwwroot/chem.wencker.top

git pull

source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate

# 如果有新的 SMILES 数据，重新生成图片
python scripts/generate_reaction_images.py
python manage.py import_reaction_images

python manage.py collectstatic --noinput
```

最后在宝塔 Supervisor 中重启 `organicchemhub`。

---

## 四、RDKit 安装排错

### `_ARRAY_API not found`

numpy 版本冲突。**必做：**

```bash
source .venv/bin/activate
pip install "numpy<2"
python -c "import numpy; print(numpy.__version__)"   # 必须是 1.x
```

### `No module named 'rdkit'`

RDKit 装到了别处，不在当前虚拟环境。检查：

```bash
which python
pip list | grep rdkit
```

如果不在虚拟环境里：`source .venv/bin/activate` 然后重装。

### `libOpenGL.so.0` 报错

Debian 12 最小安装缺 OpenGL 库：

```bash
apt-get install -y libgl1-mesa-glx libglib2.0-0
pip install --force-reinstall rdkit-pypi
```

---

## 五、关键路径

```
/www/wwwroot/chem.wencker.top/
├── .env                         # 生产配置（不提交 Git）
├── db.sqlite3                   # SQLite 数据库
├── static/images/reactions/     # 生成的 SVG 图片
├── staticfiles/                 # Nginx 直接服务的静态文件
├── scripts/generate_reaction_images.py   # SMILES→SVG 生成脚本
└── docs/deploy_v0.8_linux.md    # 本教程
```

---

## 六、日常维护速查

| 操作 | 命令 |
|------|------|
| 查看运行日志 | `tail -f /www/wwwlogs/organicchemhub.out.log` |
| 重启服务 | 宝塔 Supervisor → 重启 organicchemhub |
| 更新代码 | `git pull && source .venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput` |
| 重新生成图片 | `source .venv/bin/activate && python scripts/generate_reaction_images.py && python manage.py import_reaction_images && python manage.py collectstatic --noinput` |
| 备份数据库 | 宝塔 → 计划任务 → 每日备份 `/www/wwwroot/chem.wencker.top/db.sqlite3` |
