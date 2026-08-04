# 词航 Cihang

## Guide to Postgraduate Entrance Exam Vocabulary

**Version: v0.2**

词航（Cihang）是面向中国考研英语学习者的轻量级词汇训练网站，将每日新词、到期复习、错词修炼、学习统计和词汇地图组织成清晰的学习航线。

当前版本是无需构建工具的纯静态 MVP。学习目标和进度保存在浏览器 `localStorage` 中，适合本地使用、静态托管和宝塔服务器部署。

## 当前功能

- 今日学习航线和每日新词/复习目标
- 新词训练与间隔复习入口
- 错词修炼场、词汇地图和章节进度
- 学习统计、每日学习时长和发音偏好设置
- 浏览器本地保存学习目标和进度
- PDF 词汇数据导入脚本
- 桌面端和移动端响应式布局

v0.2 暂不包含账号登录、云端同步、数据库和管理员后台。后续设计见 [`docs/NEXT_DEVELOPMENT.md`](docs/NEXT_DEVELOPMENT.md)。

## 技术栈

- HTML5、CSS3、原生 JavaScript
- JSON 词库
- Python 3 + `pypdf`（可选，用于 PDF 词汇导入）
- 无前端构建步骤，无数据库依赖

## 本地运行

```powershell
python -m http.server 8000
```

访问 `http://localhost:8000`。Linux/macOS 使用 `python3 -m http.server 8000`。

## 云端部署：宝塔 + Xshell + GitHub

示例域名：`cihang.wencker.top`；服务器 IP：`38.95.75.185`；目录：`/www/wwwroot/cihang.wencker.top`。

### DNS

添加 A 记录：`cihang` → `38.95.75.185`。使用 `nslookup cihang.wencker.top` 检查解析。

### 宝塔创建网站

宝塔 → 网站 → 添加站点：

```text
域名：cihang.wencker.top
根目录：/www/wwwroot/cihang.wencker.top
PHP：纯静态 / 不运行 PHP
数据库：不创建
```

PHP 8.4 不是 v0.2 静态网站的运行依赖。

### Xshell 拉取仓库

```bash
cd /www/wwwroot
chattr -i /www/wwwroot/cihang.wencker.top/.user.ini 2>/dev/null || true
rm -rf /www/wwwroot/cihang.wencker.top
git clone https://github.com/wenckerwan/eng_cihang.git /www/wwwroot/cihang.wencker.top
```

若未安装 Git：`apt update && apt install -y git`。

### 权限、默认文档与 SSL

```bash
chown -R www:www /www/wwwroot/cihang.wencker.top
find /www/wwwroot/cihang.wencker.top -type d -exec chmod 755 {} \;
find /www/wwwroot/cihang.wencker.top -type f -exec chmod 644 {} \;
```

确认根目录包含 `index.html`、`app.js`、`styles.css` 和 `data/`。在宝塔默认文档中将 `index.html` 置顶；使用 Let’s Encrypt 申请证书并开启强制 HTTPS。云安全组和宝塔需放行 TCP `80`、`443`。

验证：`curl -I -H "Host: cihang.wencker.top" http://127.0.0.1`，返回 `HTTP/1.1 200 OK` 后访问 `https://cihang.wencker.top`。

## 更新、备份与回滚

备份：

```bash
cd /www/wwwroot
tar -czf cihang-backup-$(date +%Y%m%d-%H%M%S).tar.gz cihang.wencker.top
```

更新：

```bash
cd /www/wwwroot/cihang.wencker.top
git status
git pull origin main
chown -R www:www /www/wwwroot/cihang.wencker.top
git log -1 --oneline
```

回滚前先备份，再用 `git log --oneline --all` 查找目标提交。若 `.user.ini` 被设置为不可变，先用 `lsattr` 检查，再执行 `chattr -i`。

## 项目目录

```text
├── index.html              # 页面结构和学习视图
├── app.js                  # 页面切换、状态和交互逻辑
├── styles.css              # 主题、响应式布局和页脚样式
├── data/words.json         # 词汇数据
├── scripts/import_vocab.py # PDF 词汇导入
├── docs/                   # 后续开发文档
└── README.md
```

## PDF 词汇导入

```powershell
python -m pip install pypdf
python scripts/import_vocab.py ".\source.pdf" --out data/words.json
```

图片型 PDF 需要先 OCR，导入完成后请人工检查 `data/words.json`。

## 常见问题

- **403**：检查根目录、`index.html`、755 目录权限、644 文件权限和默认文档。
- **404/空白**：确认宝塔域名绑定和根目录正确，并检查浏览器 Console/Network。
- **CSS/JS 不加载**：确认资源与 `index.html` 同目录，清理浏览器缓存。
- **Git 目录已存在**：备份后检查 `.user.ini`，必要时执行 `chattr -i` 再删除。
- **域名无法访问**：检查 DNS、云安全组、宝塔端口和 SSL 域名匹配。

## 更新日志

### v0.2 - 2026-08-04

- 统一品牌为“词航 Cihang”，补充英文名称 Guide to Postgraduate Entrance Exam Vocabulary。
- 首页标题和页脚显示 `v0.2`。
- 新增作者、GitHub、个人官网和 OrganicChemHub 友情链接。
- 新增蓝白主题毛玻璃链接按钮和移动端适配。
- 完善 GitHub、宝塔、Xshell 云端部署文档。
- 新增登录、数据库和管理员后台后续开发文档。

### v0.1.0

- 完成静态词汇学习 MVP、学习统计、错词训练、词汇地图和学习设置。
- 支持浏览器本地保存学习目标与进度、静态部署和 PDF 词汇导入。

## 后续开发

计划使用 Laravel + MySQL + PHP 8.4，实现用户登录、学习数据云端同步和管理员后台。详见 [`docs/NEXT_DEVELOPMENT.md`](docs/NEXT_DEVELOPMENT.md)。

## 作者与友情链接

- 作者：wencker
- GitHub：<https://github.com/wenckerwan>
- 个人官网：<https://wencker.top>
- OrganicChemHub 丨有机化学反应与合成路线资料库：<https://chem.wencker.top/>

## License

当前项目尚未单独声明开源许可证。未经作者明确授权，请勿将项目用于商业再分发。

---

## OrganicChemHub 项目说明

OrganicChemHub 是一个面向有机化学本科生和考试学习者的学习工具，用于检索人名反应和合成路线，并提供考试提示。项目支持通过 Django admin backend 维护内容，目标是保持简洁、聚焦和持续更新。

更详细的 OrganicChemHub 项目内容请参考 `master` 分支。

### OrganicChemHub 后端依赖

```text
Django>=5.2,<5.3
gunicorn>=23.0,<24.0
rdkit-pypi>=2022.9,<2023
Pillow>=10.0
numpy<2
```

OrganicChemHub 官网：<https://chem.wencker.top/>
