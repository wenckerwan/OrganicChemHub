# OrganicChemHub v2.8 Linux 部署指南

目标环境：Debian / 宝塔面板 / Nginx / Gunicorn / Supervisor
生产目录：`/www/wwwroot/chem.wencker.top`

v2.8 运营与审计新增 `ContentBatch` 内容批次模型（迁移 `0022_contentbatch`）；更新时必须执行 `python manage.py migrate` 和 `collectstatic`。

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
rm -f reactions/migrations/0012_alter_learningresource_local_path.py
rm -f reactions/migrations/0014_merge_20260730_1535.py
rm -f reactions/migrations/0016_merge_20260802_2239.py
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_admin_roles
/www/server/panel/pyenv/bin/supervisorctl restart all
```

v2.5 新增考研专题和易混反应对比迁移 `0019_study_topics_and_comparisons`，用户互动模型迁移 `0020_user_tools_gfk`；v2.7 新增 `0021_routestep_is_key_step_and_more`（关键步骤 + 官能团关联）；v2.8 新增 `0022_contentbatch`（内容批次记录），以上更新都必须执行 `python manage.py migrate`。v2.6 无新迁移，更新时执行 `collectstatic` 即可。

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
| 考研专题 | `http://chem.wencker.top/admin/reactions/studytopic/` |
| 易混反应对比 | `http://chem.wencker.top/admin/reactions/reactioncomparison/` |

---

## 6. 备份与恢复

### 6.1 数据库备份

`db.sqlite3` 不提交 Git，更新前必须单独备份：

```bash
cd /www/wwwroot/chem.wencker.top
cp db.sqlite3 db.sqlite3.bak_$(date +%Y%m%d_%H%M%S)
```

建议保留最近 7 天的备份文件，定期清理旧备份。

### 6.2 media 文件备份

用户上传图片位于 `media/`，同样不提交 Git：

```bash
cd /www/wwwroot
tar czf chem_media_backup_$(date +%Y%m%d).tar.gz chem.wencker.top/media/
```

备份文件应存放在站点目录之外（如 `/www/backup/`）。

### 6.3 git 版本回滚

代码版本回滚（谨慎操作，先备份数据库）：

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
# 查看历史版本
git log --oneline -10
# 回滚到指定提交（保留工作区，仅移动指针）
git reset --hard <commit_hash>
python manage.py migrate
python manage.py collectstatic --noinput
/www/server/panel/pyenv/bin/supervisorctl restart all
```

> 注意：`git reset --hard` 会丢弃该提交之后的所有本地改动。如果只是暂时回退，建议使用 `git revert <commit_hash>` 生成反向提交，保留历史。

### 6.4 更新前后检查清单

更新前：

1. 备份数据库：`cp db.sqlite3 db.sqlite3.bak_$(date +%Y%m%d_%H%M%S)`。
2. 备份 media：`tar czf /www/backup/chem_media_$(date +%Y%m%d).tar.gz media/`。
3. 确认当前版本：`git log --oneline -1`。

更新后：

1. `python manage.py check` 无错误。
2. `python manage.py migrate` 无报错。
3. 前台首页、详情页可访问，静态资源正常加载。
4. 后台仪表盘、CSV 导入页可访问。

### 6.5 故障恢复

- 数据库损坏：用最近的 `db.sqlite3.bak_*` 覆盖 `db.sqlite3`，重启服务。
- 代码异常：用 `git revert` 回退到上一个稳定提交，执行 migrate + collectstatic + 重启。
- 图片丢失：用 media 备份 tar 包解压覆盖 `media/`。
