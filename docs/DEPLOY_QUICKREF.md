# 部署速查

## 推送部署

**本地 PowerShell：**

```powershell
cd D:\code_files\OrganicChemHub_dsv
git add .
git commit -m "改了什么"
git push
```

**服务器 Xshell：**

```bash
cd /www/wwwroot/chem.wencker.top
source .venv/bin/activate
git pull
python manage.py migrate
python manage.py collectstatic --noinput
/www/server/panel/pyenv/bin/supervisorctl restart all
```

## 常用后台网址

| 页面 | 地址 |
|------|------|
| 后台首页 | `http://chem.wencker.top/admin/` |
| 反应列表 | `http://chem.wencker.top/admin/reactions/reaction/` |
| 常见反应 | `http://chem.wencker.top/reactions/common/` |
| 仪表盘 | `http://chem.wencker.top/admin/reactions/reaction/dashboard/` |
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
