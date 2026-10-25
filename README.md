# ppt-rebuild · 把幻灯片截图重建成可编辑 PPTX

一个给 AI 代理用的技能（DSH skill）：给它一张幻灯片截图，它按固定工序测画布、拆图层、
重建原生形状与文本、渲染比对，产出「每个部分都能改」的 PPTX。

本仓库同时提供**完整提示词**，所以不用 DSH 的模型也能照着做。

![原图 vs 重建](examples/compare.png)

## 直接打开看效果

`examples/目录-可编辑-分层版.pptx` 就是上图那页的成品（PowerPoint / WPS / Keynote 都能开）：

- **背景**：一张完整照片（`bg_vivid.png` 反解出来的）
- **蒙版**：一层 70.5% 白的图片，三处开洞、洞底到 y=540
- **可编辑**：3 段竖排中文、3 个序号、标题、`/Contents`、黄点，全是原生文本/形状
- 删掉蒙版层就能看到完整照片；换卡片内容只需改文字

![重建结果](examples/rebuilt.png)

## 里面有什么

```
ppt-rebuild/          技能本体（放进 ~/.dsh/skills/ 即生效）
  SKILL.md            触发条件、铁律、30 秒开工、坑对照表
  README.md           安装 / 依赖 / 移植性
  references/PROMPT.md        完整提示词（给其他模型）
  references/blocks-example.json
  scripts/doctor.py   环境预检（依赖 / 渲染器 / 字体）
  scripts/render.py   pptx→PDF→PNG（绕开 1.5× 缩放 bug）
  scripts/inkcmp.py   逐块墨迹偏差 + MAE + diff
  scripts/maskfit.py  蒙版 alpha 与洞的边界（像素阶跃）
  scripts/inpaint.py  擦照片上的字
  scripts/rounded.py  异形圆角裁图
examples/             真实案例
  source.png          原截图
  rebuilt.png         重建后的渲染图
  compare.png         原图 / 重建 上下对比
  目录-可编辑-分层版.pptx   成品，可直接打开
```

## 安装

把 `ppt-rebuild/` 整个文件夹放到：

```
~/.dsh/skills/ppt-rebuild/        # Windows: %USERPROFILE%\.dsh\skills\ppt-rebuild
```

新开一个 DSH 会话，技能列表里会出现 `ppt-rebuild`。

自检：

```powershell
python "%USERPROFILE%\.dsh\skills\ppt-rebuild\scripts\doctor.py"   # 期望 "ok": true
```

## 依赖

- Python 3.9+、Pillow、numpy（DSH 自带运行时即可）
- 渲染：DSH 自带 LibreOffice Kit（自动发现），或系统 LibreOffice + PyMuPDF
- 字体：微软雅黑（必需）、华文行楷 / Bodoni MT（标题类，缺了要重标字号）

## 不用 DSH？

把 `ppt-rebuild/references/PROMPT.md` 整份发给任意能跑代码的模型，附上截图即可；
脚本是加分项。

## 它解决的问题（也是踩过的坑）

1. 把截图整张当背景 → 什么都不“可编辑”；
2. 照片里留着头标题 → 文本盖上去变两层字；
3. 阴影被压缩吃掉 → 按“边缘是白的”误判为无阴影；
4. 卡片当成叠图 → 底部出现鲜色带（实际是蒙版开洞，洞底边比卡片视觉底边高 30 px）；
5. 直接渲染 pptx 放大 1.5 倍 → 必须 convert→PDF→render。

## 许可

MIT，见 [LICENSE](LICENSE)。
