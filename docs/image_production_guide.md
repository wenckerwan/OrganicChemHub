# OrganicChemHub 图片文件制作规范 v0.5

> 本文档面向网站内容管理员，规定结构式图片的命名、规格、目录和制作流程。请所有参与图片制作的成员严格遵守本规范，确保全站图片统一、可维护。

---

## 1. 绘图工具与输出格式

| 项目 | 规范 |
|------|------|
| **绘图工具** | ChemDraw（推荐 20.x 或更新版本） |
| **输出格式** | **SVG**（可缩放矢量图形） |
| **SVG 导出方式** | ChemDraw → File → Save As → 格式选择 **SVG**（*.svg） |
| **文件扩展名** | 全小写 `.svg` |

> 禁止使用 PNG、JPG、JPEG、GIF 等栅格格式作为结构式图片。如已有 PNG 历史文件，请逐步替换为 SVG。

---

## 2. 图片命名规则

### 2.1 通用原则

- 全部使用 **小写英文字母**、**数字** 和 **下划线 `_`**
- 禁止使用中文、空格、连字符 `-`、括号或其他特殊字符
- 多个单词用下划线分隔

### 2.2 各模型命名模板

| 模型 | 字段 | 命名模板 | 示例 |
|------|------|----------|------|
| `Reaction` (人名反应) | `structure_image` | `reaction_{name_en}.svg` | `reaction_aldol.svg` |
| `SyntheticRoute` (合成路线) | `target_structure_image` | `route_{slug}.svg` | `route_aspirin.svg` |
| `RouteStep` (路线步骤) — 反应物 | `reactant_structure_image` | `step_{route_slug}_{step_number}_reactant.svg` | `step_aspirin_1_reactant.svg` |
| `RouteStep` (路线步骤) — 产物 | `product_structure_image` | `step_{route_slug}_{step_number}_product.svg` | `step_aspirin_1_product.svg` |

#### 2.2.1 关于 `name_en` 的取值规则

`name_en` 取 **该反应在数据库中 `Reaction.name_en` 字段的标准值**。例如：

| 中文名 | 英文名 (name_en) | 图片文件名 |
|--------|-------------------|-----------|
| 羟醛缩合反应 | Aldol Reaction | `reaction_aldol_reaction.svg` |
| 贝克曼重排 | Beckmann Rearrangement | `reaction_beckmann_rearrangement.svg` |
| 维蒂希反应 | Wittig Reaction | `reaction_wittig_reaction.svg` |

> 英文名中含有的空格以 `_` 替代。英文名中的大写字母在文件名中统一转为小写。  
> **例外**：如果 `name_en` 超过 60 个字符，可使用有意义的缩写（在本文档中登记备案）。

#### 2.2.2 关于 `slug` 的取值规则

`slug` 直接使用 Django 模型中的 `SlugField` 值，全小写 + 连字符 `-` 是 Django 默认行为。但在文件名中，连字符 `-` 统一替换为下划线 `_`。

---

## 3. 服务器目录结构

### 3.1 静态图片目录（手动制作，随代码部署）

```
static/
├── images/
│   ├── reactions/          # Reaction.structure_image 的手工 SVG
│   │   ├── reaction_aldol_reaction.svg
│   │   ├── reaction_beckmann_rearrangement.svg
│   │   └── ...
│   └── routes/             # SyntheticRoute & RouteStep 的手工 SVG
│       ├── route_aspirin.svg
│       └── steps/
│           ├── step_aspirin_1_reactant.svg
│           ├── step_aspirin_1_product.svg
│           └── ...
└── ...
```

### 3.2 用户上传目录（管理员在 Admin 后台上传，随媒体文件存储）

```
media/
├── reaction_structures/        # 对应 Reaction.structure_image (upload_to)
│   └── ...
├── route_structures/           # 对应 SyntheticRoute.target_structure_image (upload_to)
│   └── ...
└── route_step_structures/      # 对应 RouteStep 的 reactant/product (upload_to)
    └── ...
```

> **注意**：手工制作的 SVG 放在 `static/images/` 下，通过 `collectstatic` 部署。  
> 管理员在 Admin 上传的图片自动进入 `media/` 目录。  
> 两种方式的文件命名规则相同（见第 2 节）。

### 3.3 命名规则在 Models 中的填写建议

在 Admin 后台录入数据时：

- **`structure_image` / `target_structure_image` / `reactant_structure_image` / `product_structure_image`**：如果已在 `static/images/` 中准备了 SVG，则无需重复上传，在对应的 **URL 字段** 中填写 `/static/images/...` 路径即可。
- **`structure_image_url` / `target_structure_image_url` / `reactant_structure_image_url` / `product_structure_image_url`**：填入对应 SVG 在服务器上的路径，例如：
  ```
  /static/images/reactions/reaction_aldol_reaction.svg
  ```
- **`structure_image_caption`**：可选填，建议写反应中文名或简要说明，如 "羟醛缩合反应结构式"。

---

## 4. 图片统一规格

### 4.1 SVG 画布规格

| 参数 | 反应结构式 (Reaction) | 路线目标产物 (Route) | 路线步骤 (Step) |
|------|----------------------|---------------------|-----------------|
| **viewBox 宽度** | 0 0 600 400 | 0 0 400 300 | 0 0 600 400 |
| **viewBox 比例** | 3:2 | 4:3 | 3:2 |
| **背景** | 透明 (transparent) | 透明 | 透明 |
| **建议画布尺寸** | 600×400 px | 400×300 px | 600×400 px |

> viewBox 是 SVG 的内部坐标系，最终显示尺寸由 CSS 控制。以上为 ChemDraw 导出 SVG 时的建议画布尺寸。

### 4.2 ChemDraw 制图参数

| 参数 | 规范值 |
|------|--------|
| **键长 (Bond Length)** | 14.4 pt (0.508 cm) — ChemDraw 默认 |
| **键宽 (Bond Width)** | 1.2 pt (0.043 cm) — ChemDraw 默认 |
| **键间距 (Bond Spacing)** | 20% of bond length — ChemDraw 默认 |
| **线宽 (Line Width)** | 0.6 pt — ChemDraw 默认 |
| **边距 (Margin)** | 0.5 cm (导出时在 ChemDraw 中设置 Margins) |
| **字体** | **Arial** |
| **字号 — 原子标签** | **10 pt** |
| **字号 — 数字/电荷** | **9 pt** |
| **字号 — 箭头文字** | **10 pt** (加粗) |
| **字体样式** | Regular (不加斜体，除非是 R/S 标注等常规斜体位置) |
| **化学键颜色** | 黑色 (#000000) |
| **原子标签颜色** | 黑色 (#000000) |
| **箭头** | ChemDraw 默认实心箭头 (Bold or Full) |
| **立体化学 (楔形键)** | 使用 ChemDraw 的楔形键工具 (Wedge / Dashed) |
| **电荷标记** | 使用 `⊕` 和 `⊖` 符号，9 pt |
| **对映体/消旋体** | 在箭头标注 "rac." 或 "1) / 2)" 分步标注 |

### 4.3 化学结构绘制规范

- 每个 SVG 只包含 **一个化学转化**（一个反应物 → 产物）或 **一个目标分子**。
- 反应方程式排版顺序：**反应物 + 试剂/条件（箭头上方/下方）→ 产物**。
- 多步反应在同一图中展示时，使用多个箭头串联，箭头之间保留至少 0.5 cm 间距。
- 不显示碳原子标签（省略不写），仅显示杂原子。
- 氢原子不显示（除非用于强调立体化学）。
- 苯环使用凯库勒式（交替双键）或圆圈表示均可，但全站保持一致。**推荐使用凯库勒式（交替双键）**。
- 配体/试剂标记在箭头上下方：
  - 箭头上方：**主要试剂**
  - 箭头下方：**反应条件**（温度、溶剂等）
- 多行文字用半角逗号或换行分隔。

### 4.4 SVG 导出后检查清单

导出 SVG 后，用文本编辑器打开文件，确认：

- [ ] `<svg>` 标签包含 `xmlns="http://www.w3.org/2000/svg"`
- [ ] `viewBox` 存在且比例正确
- [ ] 无嵌入的栅格图像（无 `<image>` 标签指向 PNG/JPG）
- [ ] 文字应保存为 `<text>` 元素（而非转换为轮廓/路径）
- [ ] 文件大小不超过 **200 KB**
- [ ] 在浏览器中打开验证渲染正常

---

## 5. 制作流程

### 5.1 新图片制作步骤

```
1. 确认需求
   ↓
2. 在数据库中查找对应的 Reaction / Route / RouteStep 记录
   ↓
3. 根据第 2 节规则确定文件名
   ↓
4. 在 ChemDraw 中绘制结构式
   ↓
5. 按第 4 节参数调整格式
   ↓
6. File → Save As → SVG 导出
   ↓
7. 按第 4.4 节清单检查 SVG
   ↓
8. 放入对应目录（static/images/reactions/ 或 routes/ 或 routes/steps/）
   ↓
9. 在 Admin 中填写对应的 URL 字段（如 structure_image_url）
   ↓
10. 运行 python manage.py collectstatic（部署时）
```

### 5.2 批量制作建议

- 按反应英文名首字母分批次制作（如本周制作 A-D 开头的反应）
- 利用 `Reaction` 模型的 `name_en` 字段生成初始文件名列表
- 制作完成后运行 `python manage.py check` 确保无模型验证错误

---

## 6. 历史文件迁移计划

当前 `static/img/reactions/` 下存在约 59 个 `lecture_*.png/jpg` 文件，迁移步骤如下：

| 阶段 | 内容 |
|------|------|
| **Phase 1** (v0.5) | 确定规范、建立目录结构、准备好第一批 SVG（考研高频反应 10-15 个） |
| **Phase 2** (v0.6) | 将全部 32 个 exam_reactions 替换为 SVG |
| **Phase 3** (v0.7) | 将全部 common_reactions 替换为 SVG |
| **Phase 4** | 删除 `static/img/reactions/` 中已替换的旧 PNG 文件 |
| **最终** | 删除 `static/img/` 目录（不再使用 `lecture_*` 命名），完全迁移到 `static/images/` |

---

## 7. 常见问题

### 7.1 为什么用 SVG 而不是 PNG？

- SVG 是矢量格式，放大不失真，适合高分辨率屏幕和缩放查看
- 文件体积小（通常 10-50 KB，远小于 PNG）
- 支持 CSS 样式化和交互（后续可用 JavaScript 实现高亮等效果）
- SVG 文本可被搜索引擎索引（利于 SEO）

### 7.2 多人协作时文件名冲突怎么办？

在 `static/images/` 下按模型划分子目录，天然避免跨模型冲突。同模型内的冲突通过 `name_en` 的唯一性保证。

### 7.3 是否还需要维护文本结构式？

不需要。当前版本以后台上传的 SVG/PNG 图片作为结构式来源：
- 方程式图和缩略图是发布质量检查项。
- 机理图可选，适合需要讲解机理的反应。
- 图片缺失时应在后台补图或保持草稿，不再使用文本结构式作为降级显示。

### 7.4 SVG 可以在后台直接上传吗？

可以。在 Admin 中：
1. 使用 `structure_image` 等 FileField 直接上传 SVG 文件（上传到 `media/` 目录）
2. 或在 `structure_image_url` 中填写静态路径（`/static/images/reactions/...`）

两种方式均可，SVG 格式规则相同。

---

## 8. 附录：常用 ChemDraw 快捷键

| 操作 | 快捷键 (Windows) |
|------|-----------------|
| 绘制单键 | Click-drag (已选中 Bond 工具) |
| 绘制双键 | 在单键上再次点击 |
| 文本工具 | T |
| 选择工具 | Ctrl + 鼠标左键拖选 |
| 撤销 | Ctrl + Z |
| 重做 | Ctrl + Y |
| 立体化学 (楔形) | 右键点击键 → 选择 Wedge |
| 虚线键 | 右键点击键 → 选择 Dashed |
| 放大/缩小 | Ctrl + Shift + .  / Ctrl + Shift + , |
| 全选 | Ctrl + A |
| 对齐 | Select → Object → Align → (选择对齐方式) |

---

> **本规范版本**: v0.5  
> **最后更新**: 2026-07-29  
> **维护者**: OrganicChemHub 管理团队  
> **版本历史**: v0.5 初始版本，建立图片制作规范体系。
