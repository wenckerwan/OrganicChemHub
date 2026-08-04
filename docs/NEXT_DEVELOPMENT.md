# 词航 Cihang 后续开发文档

## 文档状态

- 当前版本：`v0.2`
- 规划起始版本：`v0.3`
- 状态：设计与实施准备阶段
- 后端路线：Laravel + MySQL
- 生产 PHP：8.4
- 角色模型：普通用户 + 管理员

## 1. 目标

将当前浏览器本地运行的静态 MVP 演进为支持账号、云端数据同步和后台管理的学习系统：

- 用户可以注册、登录、退出和找回密码。
- 学习目标、学习记录、错词和统计数据可以跨设备同步。
- 管理员可以管理用户、词库、系统配置和操作日志。
- 现有静态页面作为 UI 基础，采用渐进方式接入 API。
- 支持从 v0.2 `localStorage` 导入个人学习数据。

## 2. 技术架构

- 后端：Laravel 11+（以初始化时的最新兼容版本为准）
- PHP：8.4
- 数据库：MySQL 8.x 或 MariaDB 10.6+
- 认证：Laravel Session；前后端分离场景可使用 Sanctum
- Web：宝塔 Nginx 或 Apache
- 前端：保留现有 HTML/CSS/JavaScript，逐步增加 API 请求层
- 缓存/队列：第一阶段可选，后续使用 Redis

Laravel 生产站点根目录必须指向：

```text
/www/wwwroot/cihang.wencker.top/public
```

不要把 `.env`、源码配置或 `storage` 目录直接暴露为 Web 根目录。

## 3. 权限边界

### 普通用户

- 注册、登录、退出和修改个人资料。
- 学习新词、完成复习和管理错词。
- 设置每日新词数、复习上限和发音偏好。
- 查看个人学习统计和历史。
- 导出或导入自己的 v0.2 本地数据。

### 管理员

- 查看、禁用和恢复用户。
- 重置用户密码，但不能读取用户原始密码。
- 导入、编辑、归类和下架词汇。
- 查看全站聚合统计和系统配置。
- 查看管理员操作日志。
- 执行备份和恢复流程。

权限必须在服务端通过认证和授权中间件执行，不能只依赖前端隐藏按钮。

## 4. 数据库设计

使用 Laravel migration 管理数据库结构，生产环境禁止手工修改表结构。建议表：

| 表 | 用途 |
| --- | --- |
| `users` | 用户账号、昵称、邮箱、状态、密码哈希 |
| `roles` | 角色定义 |
| `user_roles` | 用户与角色关联 |
| `words` | 单词、词性、释义、音标、例句和状态 |
| `word_categories` | 词库、章节和来源分类 |
| `user_word_progress` | 用户掌握度、复习时间和阶段 |
| `study_sessions` | 学习会话的开始、结束和统计 |
| `study_answers` | 答题结果和间隔复习反馈 |
| `mistakes` | 用户错词、错误类型和下次复习时间 |
| `daily_goals` | 用户每日新词与复习目标 |
| `user_settings` | 用户提醒、发音和界面偏好 |
| `system_settings` | 管理员维护的系统配置 |
| `admin_operation_logs` | 管理员操作、目标资源和结果 |
| `password_reset_tokens` | 密码找回的一次性令牌 |
| `personal_access_tokens` | Sanctum 场景下的访问令牌 |

设计约束：

- 密码只保存哈希值，禁止保存明文。
- 用户名或邮箱设置唯一索引。
- 用户相关数据必须带 `user_id` 并在查询层隔离。
- 重要表增加时间、状态和关联字段索引。
- 用户删除优先使用软删除，保留统计完整性。
- 时间统一使用 UTC 存储，展示时转换为 `Asia/Shanghai`。
- 删除词汇前检查学习记录关联，优先采用下架而非物理删除。

## 5. 认证与安全

- 使用 Laravel 默认密码哈希和验证流程。
- 登录、注册、密码找回增加频率限制。
- 生产环境强制 HTTPS，Cookie 设置 `Secure`、`HttpOnly` 和合适的 `SameSite`。
- 开启 CSRF 保护。
- 后台路由必须经过认证、角色和权限中间件。
- 生产环境设置 `APP_DEBUG=false`。
- `.env`、数据库密码、Token 和证书私钥不得提交 GitHub。
- 日志不得记录密码、完整 Token 或敏感请求体。
- 数据库账号采用最小权限。
- 管理员重要操作写入操作日志。

## 6. API 规划

### 认证和个人资料

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/me
PUT  /api/me
POST /api/auth/forgot-password
POST /api/auth/reset-password
```

### 学习功能

```text
GET  /api/words
GET  /api/words/{id}
GET  /api/study/today
POST /api/study/sessions
POST /api/study/answers
GET  /api/stats/overview
GET  /api/mistakes
PUT  /api/mistakes/{id}
GET  /api/settings
PUT  /api/settings
POST /api/data/import
GET  /api/data/export
```

### 管理后台

```text
GET    /api/admin/users
PUT    /api/admin/users/{id}/status
POST   /api/admin/words
PUT    /api/admin/words/{id}
DELETE /api/admin/words/{id}
GET    /api/admin/stats
GET    /api/admin/logs
```

接口统一返回 JSON；列表接口支持分页、搜索和排序；参数校验使用 Form Request；错误响应使用统一错误码；响应中不得包含密码、Token 等敏感字段。

## 7. 前端迁移策略

1. 保留 v0.2 页面和视觉语言。
2. 抽离词汇、学习进度、统计和设置的数据访问函数。
3. 新增 API client，统一处理认证失效、网络错误和 JSON 错误。
4. 登录前显示登录/注册入口，未登录时可保留游客模式。
5. 登录后从 API 读取用户数据，避免 API 失败时静默覆盖本地数据。
6. 提供本地 `localStorage` JSON 导出和登录后导入。
7. 导入过程校验格式、按用户隔离，并采用事务保证失败回滚。
8. API 和静态模式必须有清晰的加载、空状态和错误状态。

## 8. v0.2 数据迁移

导入格式应包含版本号：

```json
{
  "schema_version": 1,
  "source": "cihang-v0.2-localStorage",
  "exported_at": "2026-08-04T00:00:00Z",
  "goals": {},
  "progress": [],
  "mistakes": []
}
```

导入前保留原始本地数据，校验字段和数量上限；重复记录采用幂等处理；返回成功、跳过、失败数量及原因；新字段通过 schema 版本升级，不直接破坏旧数据。

## 9. 宝塔生产部署

先在宝塔创建 MySQL 数据库和独立数据库用户，再执行：

```bash
cd /www/wwwroot/cihang.wencker.top
composer install --no-dev --optimize-autoloader
cp .env.example .env
php artisan key:generate --force
php artisan migrate --force
php artisan storage:link
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

宝塔配置：

- 网站根目录：`/www/wwwroot/cihang.wencker.top/public`
- PHP：8.4
- `.env`：生产数据库、域名和邮件配置
- `storage`、`bootstrap/cache`：由 Web 用户可写
- HTTPS：部署证书并强制跳转
- 定时任务：执行 Laravel scheduler
- 队列：需要异步任务时启用 Supervisor/队列进程

发布前必须备份数据库和项目目录，发布后执行首页、登录、学习、后台权限和数据库连接冒烟测试。

## 10. 测试计划

后端和 API 需要覆盖注册、登录、退出、密码找回、限流、普通用户越权、用户数据隔离、管理员用户管理、词汇管理、学习记录、错词、统计和 migration。前端和部署需要覆盖 v0.2 交互回归、本地数据导入导出、移动端无横向溢出、HTTPS、`public` 根目录和数据库备份恢复。

建议使用 PHPUnit、Laravel Feature Tests、浏览器端到端测试和部署冒烟脚本。

## 11. 发布、备份与回滚

发布前创建 Git tag，备份数据库、上传文件和 `.env` 安全副本，检查 PHP 扩展、队列、定时任务、HTTPS 和 migration。

回滚时切换上一版本代码，必要时执行反向迁移，恢复数据库备份，清理 Laravel 缓存，再检查登录、学习和后台权限。生产环境不使用 `git reset --hard` 作为常规发布方案。

## 12. 版本路线

### v0.3：账号和云端数据基础

初始化 Laravel 和 MySQL；完成注册、登录、退出、资料和角色；建立词汇、进度、学习记录、每日目标表；提供基础认证 API 和数据迁移接口。

### v0.4：学习数据全面云端化

前端接入学习 API；实现多设备同步、错词同步和统计；完成 v0.2 `localStorage` 导入导出；增加加载、空状态和网络错误。

### v0.5：管理员后台

完成用户管理、词库导入编辑、全站统计、系统配置和管理员操作日志。

### v1.0：生产增强

加入数据库自动备份与恢复演练、Redis 缓存和队列、邮件通知、限流、监控、安全审计和正式开源许可证。

## 13. 验收标准

- 用户可注册、登录、退出并找回密码。
- 普通用户不能访问管理员功能或其他用户数据。
- 学习、错词、目标和统计数据可靠保存。
- 管理员可以管理用户和词库，关键操作有日志。
- v0.2 本地数据可以校验后导入云端。
- migration、备份和恢复流程经过实际测试。
- 生产环境使用 HTTPS，Debug 关闭，敏感配置不进 Git。
- 宝塔部署可由另一台同规格服务器按文档复现。

## 14. 相关链接

- GitHub：<https://github.com/wenckerwan>
- 个人官网：<https://wencker.top>
- OrganicChemHub：<https://chem.wencker.top/>
