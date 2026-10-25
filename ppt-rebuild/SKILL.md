---
name: ppt-rebuild
description: Use when the user hands over a screenshot of a slide (or a reference page) and wants an editable PPTX that matches it — measure the canvas, decide whether it is "photo + mask" or "cards on top", rebuild every element as native shapes/text/pictures, then render and compare block by block. Ships scripts for LibreOffice rendering, ink comparison, mask fitting, text removal and rounded crops, plus the full prompt in references/PROMPT.md.
---

# PPT 截图 → 可编辑 PPTX（可执行版）

完整提示词：`references/PROMPT.md`（13 节 + Part A–H + 复盘）。本文件是它的**操作版**，
只写"我会怎么做"，以及每个坑对应的动作。

## 何时用

- 用户发一张幻灯片截图，说"做成 ppt / 复刻 / 每个部分可编辑"；
- 用户说"照着你的提示词做"（先读 references/PROMPT.md，再按本流程执行）；
- 需要把参考页（PPT/PDF/图片）重建成可编辑页面。

## 铁律（每条都踩过）

1. **零整图**：文字、线条、形状必须是原生对象；只允许照片、抠图装饰作为图片。
2. **文字真文本**：竖排用 `bodyPr vert="eaVert"`；数字、标题、序号都不能烘焙。
3. **效果测到就要复现**：阴影/发光用 `a:effectLst`（`outerShdw`），没测到不许加。
4. **照片层必须零字形**：标题、水印、页码也要擦；否则真文本盖上去就是两层字。
5. **先拆图层**：是"照片"，还是"照片 + 蒙版"？卡片更艳、周围更淡 → 多半是蒙版开洞。
6. **洞的边界按像素阶跃找**，不按卡片视觉轮廓：本例洞底 540，卡片视觉底边 573。
7. **反解蒙版只作参考**：`P=(O−255a)/(1−a)` 会把噪声放大 1/(1−a) 倍；带渐变/羽化的蒙版优先烘焙。
8. **渲染必须 convert→PDF→render**：本机直接 render pptx 会 1.5× 缩放。
9. **字号用校准页反推**，不靠猜（见下）。
10. **渲染比对 2–3 轮**：文本块偏差 ≤1 px，同源页面 MAE ≤4。

## 30 秒开工

1. 量画布：去掉截图白边 → 归一到 16:9（13.333×7.5 in）。
2. 量元素：卡片/文字/序号/装饰的外接框（像素），存 JSON。
3. 判图层：`scripts/maskfit.py` 估蒙版 alpha 与洞底边。
4. 做素材：`scripts/inpaint.py` 擦字、`scripts/rounded.py` 圆角裁图、反解出鲜色底图。
5. 写 build 脚本：单位换算（`ex/ey/pt`）+ 文本框（不换行/零边距/固定行距）+ 竖排 + 阴影 XML。
6. 渲染：`scripts/render.py deck.pptx preview --width 1022`。
7. 比对：`scripts/inkcmp.py source.png preview/page-0001.png --blocks blocks.json --out diff.png`。
8. 调 CALIB 偏移 → 重渲染，直到每块 ≤1 px。
9. 交付：pptx + preview + compare + build 脚本 + assets。

## 脚本

| 脚本 | 用途 | 例子 |
|---|---|---|
| `doctor.py` | 环境预检：依赖 / 渲染器 / 字体 | `python doctor.py`（`"ok": true` 才算齐） |
| `render.py` | pptx→PDF→PNG，按设计画布尺寸输出 | `python render.py deck.pptx out --size 1022x578 --dpi 192` |
| `inkcmp.py` | 逐块墨迹偏差 + MAE + diff | `python inkcmp.py src.png out/page-0001.png --blocks blocks.json --out diff.png` |
| `maskfit.py` | 估蒙版 alpha、洞的左右/底边 | `python maskfit.py slide.png --cards "135,107,335,574;..."` |
| `inpaint.py` | 擦掉照片上的字（BFS 邻居填充） | 白字：`--box ... --out x.png`；深色字/橙字：`--mode dark --thr 185` |
| `rounded.py` | 异形圆角裁图（带 alpha） | `python rounded.py src.png --box 61,378,341,626 --radii 75,0,0,0 --out card1.png` |

blocks.json 的 block：`{"name":"title","box":[x0,y0,x1,y1],"mode":"dark"|"light"|"orange","thr":200}`。
`mode=light` 用于白字（卡片里的竖排/序号），`dark` 用于深色标题，`orange` 用于品牌橙。

## 字号校准（不猜）

1. 新建一页白底，挑 4–6 个字号，同一字符串各一行（行距 ≥ 字号×1.6）。
2. `render.py` 出图。
3. 用 `inkcmp.py` 量每行墨迹宽/高（或写 20 行 numpy 直接量）。
4. 目标宽 ÷ 实测宽 × 字号 = 新字号；字距用 `(目标宽 − 实测宽)/(n−1)/1.07 pt` 补。
5. 竖排文字：字号控制字宽，`spc` 控制字间节距（本例 40 pt + 7.4 pt → 节距 48）。

## 常见坑与动作

| 现象 | 原因 | 动作 |
|---|---|---|
| 渲染整体放大 1.5×、右边被裁 | 直接 render pptx 的 bug | 先 convert 成 PDF 再 render |
| 标题发粗/发脏 | 照片里还留着旧标题 | `inpaint.py` 擦掉再上文本 |
| 卡片底部一条鲜色带 | 洞按视觉底边开 | `maskfit.py` 找阶跃，洞底改到 540 |
| 阴影消失 | 误以为"不加效果" | 测环形差值，`outerShdw` 复现 |
| 不同渲染器偏色 | 半透明层叠加 | 把蒙版/压暗烘焙进照片 |
| 竖排字不竖 | 只设了旋转 | `bodyPr vert="eaVert"` |

## 交付清单

- `.pptx`（对象清单：类型/位置/尺寸/可编辑性）
- `preview/`（渲染图、diff、compare 并排）
- `scripts/build_*.py`（可重跑）、`assets/`（底图、蒙版、卡片）
- 回复里写清：每部分怎么改、已知差异、字体替代

## 参考

- `references/PROMPT.md`：完整提示词（给其他模型用）。
- 本技能目录：`~/.dsh/skills/ppt-rebuild`（Windows: `%USERPROFILE%\.dsh\skills\ppt-rebuild`）。
