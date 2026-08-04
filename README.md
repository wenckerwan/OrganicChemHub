# English One Vocabulary

English One is a lightweight, game-inspired vocabulary learning website for Chinese postgraduate entrance exam English learners. It helps users build a daily study habit through customizable new-word and review goals, spaced repetition practice, mistake review, progress tracking, and a vocabulary journey map.

This project is currently a private MVP built with plain HTML, CSS, and JavaScript. Learning goals and progress are stored locally in the browser, making it easy to run locally or deploy as a static website.

## Quick Start

```powershell
python -m http.server 8000
```

Open `http://localhost:8000` in your browser.

## Deployment

The project can be deployed to any static hosting service, including GitHub Pages, Vercel, Netlify, or a traditional web server. Use the project root as the publish directory.

---

# 词航 · 考研英语一高频词汇

这是一个无需构建工具即可运行的学习网站 MVP。它包含今日航程、词汇学习、四阶段产品规划中的核心游戏化界面、词汇地图、错词修炼场、统计和每日目标设置。

## 运行

直接用浏览器打开 `index.html` 即可。也可以在项目目录运行：

```powershell
python -m http.server 8000
```

然后打开 http://localhost:8000 。学习目标和答题进度会保存在浏览器 `localStorage` 中。

## PDF 导入

环境安装 `pypdf` 后，可从带批注 PDF 生成保留来源页码的 JSON：

```powershell
python scripts/import_vocab.py ".\考研英语 2000-2026 英一工具包_withMarginNotes.pdf" --out data/words.json
```

导入器保留原始片段供人工校验。2026 图片型 PDF 需要后续 OCR，不会阻塞当前 MVP。
