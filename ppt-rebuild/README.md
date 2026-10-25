# ppt-rebuild · 安装与分发

一个 DSH 技能：把幻灯片截图复建成「每个部分都可编辑」的 PPTX。
本目录即完整技能包，拷给别人时只需整个文件夹。

## 一、给同样用 DSH 的人（推荐）

1. 拿到 `ppt-rebuild` 文件夹（或 `ppt-rebuild.zip`）；
2. 解压/复制到：

   ```
   C:\Users\<用户名>\.dsh\skills\ppt-rebuild\
   ```

   目录里应能直接看到 `SKILL.md`、`scripts\`、`references\`；
3. 重启 DSH 会话（或新开一个会话）——技能目录里会出现 `ppt-rebuild`；
4. 自检：让模型「用 ppt-rebuild 把这张截图做成 ppt」，它应当先 `skill ppt-rebuild`。

> 技能在会话启动时扫描 `~/.dsh/skills/*/SKILL.md`，改完不用装任何依赖。

## 二、依赖

| 依赖 | 必需 | 说明 |
|---|---|---|
| Python 3.9+ 与 Pillow、numpy | 是 | DSH 自带运行时即可；系统 Python 需 `pip install pillow numpy` |
| LibreOffice Kit（DSH 自带） | 渲染用 | `scripts/render.py` 会自动找 `<home>\deepseek\resources\...` 下的 node + kit |
| 或系统 LibreOffice + PyMuPDF | 渲染用 | 无 DSH 时：`soffice` 在 PATH，`pip install pymupdf` |

环境变量（可选，路径不同时再设）：

```powershell
$env:DSH_NODE = 'C:\...\node.exe'
$env:DSH_KIT  = 'C:\...\libreoffice-kit\lib\cli.js'
$env:DSH_SOFFICE = 'C:\Program Files\LibreOffice\program\soffice.exe'
```

## 三、给不用 DSH 的人

把 `references/PROMPT.md` 整份发给对方即可——它是自包含的提示词（坐标系、分部件做法、
验收标准、负向清单都在里面），配合截图就能照做；`scripts/` 是加分项，不是必需。

## 四、验证安装

```powershell
$py = '<python.exe>'
$sk = "$env:USERPROFILE\.dsh\skills\ppt-rebuild"

& $py "$sk\scripts\doctor.py"     # 先跑这个：依赖 / 渲染器 / 字体
& $py "$sk\scripts\render.py" 你的.pptx out --size 1022x578
& $py "$sk\scripts\inkcmp.py" 原图.png out\page-0001.png --blocks "$sk\references\blocks-example.json"
& $py "$sk\scripts\maskfit.py" 原图.png --cards "135,107,335,574;410,107,611,574;686,107,886,574"
```

四条命令分别验证：环境、渲染、比对、蒙版测量。`doctor.py` 输出 `"ok": true` 才算齐活。

## 五、能不能做到「和我这里一样」

**方法、脚本行为、交付结构是确定一致的；像素级结果取决于三件事：**

| 变量 | 影响 | 怎么消掉 |
|---|---|---|
| 字体（微软雅黑 / 华文行楷 / Bodoni MT / Arial） | 缺字体 → 字号和字距要重新标定，否则文字块偏差 3–10 px | `doctor.py` 会列缺哪个；按 SKILL.md「字号校准」重跑一遍 |
| 渲染器（LibreOffice Kit 的版本 / soffice 版本） | 预览图色差 2–8 级；PPTX 本身不受影响 | 交付以 PPTX 为准；比对只看几何和文字块 |
| 画布是否精确 16:9 | 用 `--size 原图宽x高`，不要只给 `--width` | 见 `render.py` 注释 |

模型能否严格照做也有影响：SKILL.md 里把判据写成了「数值门限」（≤1 px、MAE ≤4、
OCR 零字、4× 放大看阴影），就是为了让不同模型执行时结果收敛。

## 六、怎么打包分发

```powershell
Compress-Archive -Path "$env:USERPROFILE\.dsh\skills\ppt-rebuild" `
                 -DestinationPath "$env:USERPROFILE\Desktop\ppt-rebuild.zip" -Force
```

对方解压后把文件夹放到自己的 `~\.dsh\skills\` 下即可。

## 七、内容清单

```
ppt-rebuild/
  SKILL.md                    技能说明（触发条件、铁律、30 秒开工、坑表）
  README.md                   本文件
  references/PROMPT.md        完整提示词（给其他模型用）
  references/blocks-example.json   inkcmp 的区块模板
  scripts/doctor.py           环境预检（依赖/渲染器/字体）
  scripts/render.py           pptx→PDF→PNG（自动找 kit / soffice）
  scripts/inkcmp.py           逐块墨迹偏差 + MAE + diff
  scripts/maskfit.py          蒙版 alpha 与洞的边界（像素阶跃）
  scripts/inpaint.py          擦照片上的字（白字/深字）
  scripts/rounded.py          异形圆角裁图
```
