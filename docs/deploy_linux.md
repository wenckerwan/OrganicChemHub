# OrganicChemHub v2.3 Linux 部署指南

目标环境：Debian / 宝塔面板 / Nginx / Gunicorn / Supervisor
生产目录：`/www/wwwroot/chem.wencker.top`

v2.3 新增前台访问统计，服务器部署不需要额外安装依赖；更新时执行数据库迁移即可。

---

## 1. 首次部署

```bash
cd /www/wwwroot
git clone https://github.com/wenckerwan/OrganicChemHub.git chem.wencker.top
cd /www/wwwroot/chem.wencker.top

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp deploy/chem.wencker.top.env.example .env
python - <<'PY'
from pathlib import Path
from django.core.management.utils import get_random_secret_key

env = Path(".env")
text = env.read_text(encoding="utf-8")
text = text.replace("replace-this-with-a-long-random-secret-key", get_random_secret_key())
env.write_text(text, encoding="utf-8")
print("SECRET_KEY generated")
PY

python manage.py migrate
python manage.py setup_admin_roles
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

如果包源较慢：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

---

## 2. 日常更新

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
git pull origin master
pip install -r requirements.txt
rm -f reactions/migrations/0016_merge_20260802_2239.py
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_admin_roles
/www/server/panel/pyenv/bin/supervisorctl restart all
```

可选：发布已经补全的草稿内容。

```bash
python manage.py publish_ready_content --dry-run
python manage.py publish_ready_content
```

---

## 3. 宝塔 Nginx 配置

宝塔网站根目录设置为：

```text
/www/wwwroot/chem.wencker.top
```

反向代理目标：

```text
http://127.0.0.1:8000
```

推荐在站点配置文件中保留静态文件和媒体文件规则：

```nginx
location /static/ {
    alias /www/wwwroot/chem.wencker.top/staticfiles/;
    expires 30d;
    access_log off;
}

location /media/ {
    alias /www/wwwroot/chem.wencker.top/media/;
    expires 7d;
}

location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

保存后检查并重载：

```bash
nginx -t
/etc/init.d/nginx reload
```

如果出现 `duplicate location "/"`，说明宝塔反向代理文件和手写 `location /` 重复。保留一种方式即可。

---

## 4. Supervisor

常用命令：

```bash
/www/server/panel/pyenv/bin/supervisorctl status
/www/server/panel/pyenv/bin/supervisorctl restart all
/www/server/panel/pyenv/bin/supervisorctl tail organicchemhub:organicchemhub_00 stderr
```

确认本机 Django 服务：

```bash
curl -I http://127.0.0.1:8000/
```

确认 Nginx 反代：

```bash
curl -I -H "Host: chem.wencker.top" http://127.0.0.1/
```

---

## 5. 常用后台入口

| 页面 | 地址 |
|------|------|
| 后台首页 | `http://chem.wencker.top/admin/` |
| 内容质量仪表盘 | `http://chem.wencker.top/admin/reactions/dashboard/` |
| CSV 导入 | `http://chem.wencker.top/admin/reactions/import/` |
| 图片维护 | `http://chem.wencker.top/admin/reactions/images/` |
| 消息群发 | `http://chem.wencker.top/admin/operations/messages/send/` |
| 消息清理 | `http://chem.wencker.top/admin/operations/messages/cleanup/` |
| 访问统计 | `http://chem.wencker.top/admin/reactions/visitcounter/` |

---

## 6. 备份建议

更新前备份数据库：

```bash
cd /www/wwwroot/chem.wencker.top
cp db.sqlite3 db.sqlite3.bak_$(date +%Y%m%d_%H%M%S)
```

用户上传图片位于：

```text
/www/wwwroot/chem.wencker.top/media/
```

`db.sqlite3` 和 `media/` 不提交 Git，需要单独备份。
