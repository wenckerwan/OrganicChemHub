# 部署速查

## 推送部署

**本地 PowerShell：**

```powershell
cd D:\code_files\OrganicChemHub_dsv
git add .
git commit -m "v2.1: 内容发布完善 - 前台状态与自动发布工具"
git push
```

**服务器 Xshell：**

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_admin_roles
/www/server/panel/pyenv/bin/supervisorctl restart all
```

## 常用后台网址

| 页面 | 地址 |
|------|------|
| 后台首页 | `http://chem.wencker.top/admin/` |
| 人名反应后台 | `http://chem.wencker.top/admin/reactions/namedreaction/` |
| 常见反应后台 | `http://chem.wencker.top/admin/reactions/generalreaction/` |
| 仪表盘 | `http://chem.wencker.top/admin/reactions/dashboard/` |
| 消息管理 | `http://chem.wencker.top/admin/reactions/message/` |
| 反馈管理 | `http://chem.wencker.top/admin/reactions/feedback/` |
| 导航菜单 | `http://chem.wencker.top/admin/reactions/navitem/` |

## 常用命令

```bash
# 查看 Git 状态
git status

# 查看错误日志
tail -30 /www/wwwlogs/organicchemhub.err.log

# 查看运行日志
/www/server/panel/pyenv/bin/supervisorctl tail organicchemhub:organicchemhub_00 stderr

# 重启服务
/www/server/panel/pyenv/bin/supervisorctl restart organicchemhub:organicchemhub_00
```
