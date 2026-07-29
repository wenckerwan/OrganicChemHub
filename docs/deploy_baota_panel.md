# OrganicChemHub 宝塔面板部署指南

本文档用于第一次把 OrganicChemHub 部署到宝塔面板管理的 Linux 服务器。

## 1. 你的服务器信息

- 域名：`chem.wencker.top`
- 网站目录：`/www/wwwroot/chem.wencker.top`
- 程序端口：`127.0.0.1:8000`
- 管理后台：`https://chem.wencker.top/admin/`

部署前先确认：

- 域名 A 记录已经指向服务器公网 IP。
- 宝塔已创建网站 `chem.wencker.top`。
- 宝塔已安装 Nginx、Python 项目管理器或 Supervisor 管理器。
- 如果启用 HTTPS，先在宝塔网站 SSL 页面申请并开启证书。

## 2. 上传代码

在 Xshell 连接服务器后，把 GitHub 仓库放到网站目录：

```bash
cd /www/wwwroot
git clone 你的GitHub仓库地址 chem.wencker.top
```

如果目录已经存在，则进入目录后更新代码：

```bash
cd /www/wwwroot/chem.wencker.top
git pull
```

## 3. 首次安装命令

从 Xshell 执行：

```bash
cd /www/wwwroot/chem.wencker.top
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
cp deploy/chem.wencker.top.env.example .env
python - <<'PY'
from pathlib import Path
from django.core.management.utils import get_random_secret_key
env_path = Path(".env")
text = env_path.read_text(encoding="utf-8")
text = text.replace("replace-this-with-a-long-random-secret-key", get_random_secret_key())
env_path.write_text(text, encoding="utf-8")
PY
python manage.py migrate
python manage.py loaddata common_reactions
python manage.py loaddata exam_reactions
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

说明：`.env` 会被 Django 自动读取，里面保存生产环境配置。它不会提交到 GitHub。

## 4. 临时启动测试

先用下面命令确认网站程序能启动：

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
gunicorn organic_chem_hub.wsgi:application --chdir /www/wwwroot/chem.wencker.top --bind 127.0.0.1:8000 --workers 2
```

看到 Gunicorn 正常运行后，不要关闭 Xshell，先到宝塔配置反向代理。测试通过后按 `Ctrl+C` 停止临时服务，再配置长期运行。

## 5. 宝塔反向代理

在宝塔面板中进入：

```text
网站 -> chem.wencker.top -> 反向代理 -> 添加反向代理
```

填写：

```text
目标 URL：http://127.0.0.1:8000
发送域名：$host
```

然后进入该网站的配置文件，确认有静态文件规则：

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
```

完整 Nginx 示例见 `deploy/nginx_chem.wencker.top.conf`。宝塔已经生成 SSL 配置时，不要整段覆盖，只复制需要的 `location` 配置。

## 6. 长期运行方式

推荐使用宝塔 Supervisor 管理器。添加守护进程时填写：

```text
名称：organicchemhub
运行目录：/www/wwwroot/chem.wencker.top
启动用户：www
启动命令：/www/wwwroot/chem.wencker.top/.venv/bin/gunicorn organic_chem_hub.wsgi:application --chdir /www/wwwroot/chem.wencker.top --bind 127.0.0.1:8000 --workers 2 --timeout 60
```

Supervisor 配置文件模板见：

```text
deploy/supervisor_organicchemhub.conf
```

如果你使用宝塔 Python 项目管理器，也使用同一个启动命令，项目根目录选择 `/www/wwwroot/chem.wencker.top`。

## 7. 学习资料索引

你本机资料目录是：

```text
F:\2027考研资料\有机化学
```

服务器不能直接读取这个 Windows 路径。若需要在服务器展示资料索引，请先把资料上传到服务器目录，例如：

```text
/www/wwwroot/chem.wencker.top_private/organic_chemistry
```

再执行：

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
python manage.py index_learning_resources "/www/wwwroot/chem.wencker.top_private/organic_chemistry"
```

如果暂时不上传资料，可以跳过这一步，网站其他功能不受影响。

## 8. 更新代码

以后从 GitHub 同步新版本时：

```bash
cd /www/wwwroot/chem.wencker.top
git pull
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python manage.py migrate
python manage.py loaddata common_reactions
python manage.py loaddata exam_reactions
python manage.py collectstatic --noinput
```

然后在宝塔 Supervisor 或 Python 项目管理器中重启 `organicchemhub`。

## 9. 常见问题

- 打开域名显示 502：检查 Gunicorn/Supervisor 是否运行，端口是否为 `127.0.0.1:8000`。
- 静态样式不显示：检查 `collectstatic` 是否执行，Nginx `/static/` 是否指向 `staticfiles`。
- 后台上传的结构式图片不显示：检查 Nginx `/media/` 是否指向 `/www/wwwroot/chem.wencker.top/media/`。
- 后台无法登录：确认 `python manage.py migrate` 已执行，并已创建超级管理员。
- 表单提交出现 CSRF 错误：检查 `.env` 中 `DJANGO_CSRF_TRUSTED_ORIGINS` 是否包含当前访问协议和域名。
- 搜索没有内容：执行 `python manage.py loaddata common_reactions exam_reactions`，并确认内容状态为“已发布”。

## 10. 备份建议

- 宝塔计划任务每日备份 `/www/wwwroot/chem.wencker.top/db.sqlite3`。
- 更新代码前备份 `.env`、`db.sqlite3` 和 `media/`。
- 大批量导入学习资料索引前，先备份数据库。
