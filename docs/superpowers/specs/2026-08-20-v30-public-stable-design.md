# v3.0 公开稳定版设计规格

## 1. 版本信息

- 版本：v3.0
- 标题：公开稳定版 - 内容上线工作流与发布基线
- 日期：2026-08-20
- 基准版本：v2.8（已完成，2026-08-20）

## 2. 现状盘点

| v3.0 目标条目 | 现状 | 差距 |
|---|---|---|
| 反应库达到稳定规模 | 43 条人名反应 + 42 条常见反应，**已发布 0 条** | 🔴 全部缺 `equation_img`/`thumbnail_img`，无法通过发布校验 |
| 路线库达到稳定规模 | 仅 1 条已发布 | 🟡 内容运营问题（工具已齐） |
| 专题学习入口完整 | 功能与空状态齐备，0 个专题、0 组对比 | 🟡 内容运营问题 |
| 后台质量看板常态化 | 仪表盘 + OpLog + ContentBatch 已具备 | 🟢 需增加占位图待替换计数 |
| 部署、备份、恢复文档 | v2.8 已完善备份恢复章节 | 🟢 微调 |

**核心瓶颈**：85 条反应全部缺图 → 发布就绪数为 0 → 前台几乎空白。
项目方向已声明"不再规划文本结构式生成、结构编辑器或子结构检索路线"（以图片上传为准），因此 v3.0 提供**占位图生成 + 图片维护工作流**，让内容可先上线、再逐步替换真图，形成可长期运营的公开网站。

## 3. 产品目标

1. 管理员可一键为缺图反应生成占位图，使内容通过发布校验并上线。
2. 图片维护工具支持按缺失类型筛选与批量操作，占位图可被识别、被替换。
3. 提供内容就绪报告命令，逐条列出缺失项，指导补图与发布。
4. 发布命令与后台批量发布行为一致，写入操作日志与内容批次。

## 4. 实现范围

### 4.1 占位图服务（`reactions/services/placeholder.py`）

- `equation_svg(title)`：生成 1200×360 SVG，浅色虚线框 + 反应中文名 + "方程式图片待补充"提示。
- `thumbnail_svg(title)`：生成 400×300 SVG，品牌底色 + 名称首字。
- `placeholder_for(instance)`：按路径约定 `reaction_images/placeholder/reaction_{slug}_{kind}.svg` 写入 `MEDIA_ROOT`，绑定 `equation_img`/`thumbnail_img` 字段并保存，返回绑定字段名列表。
- 占位图路径含 `placeholder/` 目录段，作为"待替换"标记，与真实上传图区分。

### 4.2 图片维护工具增强（`reactions/admin_tools.py` + 模板）

- 支持 `?missing=equation|thumbnail|mechanism` 类型筛选。
- 列表全量展示（分页，替换原 50 条截断）。
- POST `generate_placeholders`：为选中反应批量生成占位图，写入 OpLog（action=`placeholder_generate`）与 ContentBatch（kind=`other`，summary="批量生成占位图"）。

### 4.3 内容就绪报告命令（`reactions/services/readiness.py` + 管理命令）

- `readiness.summary()`：各反应库统计 total / ready / missing_fields / missing_images / placeholder_count。
- `readiness.export_rows()`：逐条（模型、名称、slug、状态、缺项、是否占位图、可发布）。
- 管理命令 `content_readiness_report`：默认控制台统计；`--export path.csv` 导出逐条清单。

### 4.4 发布流程闭环

- `publish_ready_content` 命令发布成功后写 OpLog（action=`publish`）与 ContentBatch（kind=`publish`），与 v2.8 后台批量发布行为一致。
- 仪表盘增加 `placeholders_pending` 计数（占位图待替换数）。

## 5. 明确不做

- 不做结构式自动生成（方向已声明放弃）。
- 不新增模型、不新增迁移（零模型变更，v3.0 无数据库迁移）。
- 不做前台功能改动（空状态已全覆盖）。
- 不引入第三方库。

## 6. 验收标准

- 管理员可在图片维护页筛选缺图反应，一键批量生成占位图并发布。
- 占位图可被仪表盘/报告识别为"待替换"。
- `content_readiness_report` 输出准确统计与逐条 CSV。
- 全量测试通过，`manage.py check` 无问题，无未生成迁移。
