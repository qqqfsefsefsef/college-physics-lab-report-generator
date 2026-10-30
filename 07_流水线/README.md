# 实验报告流水线 · M1

一句话：**内容只生成一次，格式只是渲染；数字只由代码算，模型只写文字；读图结果必须过闸门。**

## 目录

```
07_流水线/
├─ pipeline.py            CLI：init / import / review / confirm / calc / render / status / all
├─ core.py                项目目录、闸门检查、计算（lsq / review / calc_*）
├─ experiments/
│  └─ tungsten.json       实验定义：表格结构、图、勘误、公认值、处理范式
└─ projects/
   └─ tungsten-2026-10-13/
      ├─ source/          原始照片（默认不入库）
      ├─ data.json        ② 读图结果 + 置信度 + 待确认清单
      ├─ review.html      ③ 核对清单（人看的）
      ├─ calc.json        ④ 计算结果 + 渲染器输入（同构）
      ├─ meta.json        ⓪ 格式选择 / 闸门状态 / 步骤时间 / 版本 / 模型
      └─ out/             ⑥ 渲染产物：报告.docx、报告_打印版.html、verify.txt
```

## 七个阶段

| 阶段 | 命令 | 产物 | 守则 |
|---|---|---|---|
| ⓪ 选格式 | `init --formats docx,html` | meta.formats | 勾几个都不涨价 |
| ① 素材 | （拖进 `source/`） | — | 原图默认不上传 |
| ② 读 | `import --from <json>` | data.json | 视觉模型或手工，**都会错** |
| ③ 闸门 | `review` → `confirm` | review.html、meta.gate | 未确认不许往下走 |
| ④ 算 | `calc` | calc.json | 只有代码算，可复现 |
| ⑤ 写 | （本版：`04/content_*.md`） | 正文 md | 模型不碰数字 |
| ⑥ 渲染 | `render --formats docx,html` | out/ | 同一份内容，多格式 |
| ⑦ 存档 | （项目目录本身） | 全部 | 可重算、可重渲染、可追溯 |

## 跑一遍

```bash
cd 07_流水线
python pipeline.py init    --exp tungsten --slug tungsten-2026-10-13 --date 2026-10-13
python pipeline.py import  --slug tungsten-2026-10-13 --from ../04_生成过程_脚本图表/data_tungsten.json
python pipeline.py review  --slug tungsten-2026-10-13
python pipeline.py confirm --slug tungsten-2026-10-13 --all --note "已逐格核对"
python pipeline.py calc    --slug tungsten-2026-10-13
python pipeline.py render  --slug tungsten-2026-10-13 --formats docx,html --name 钨的逸出功测定
python pipeline.py status  --slug tungsten-2026-10-13
```

一条龙：`python pipeline.py all --slug ... --exp tungsten --from <json> --note "..."`

## 闸门规则

`core.review()` 产出的条目分三级：

- **block**：不确认就不能算（如：标记了待确认却还没给值）→ `calc/render` 直接拒绝；
- **warn**：建议确认（行内非单调、量级跳变、表 2 与 lg(表1) 对撞、行数少一行）；
- **info**：仅提示（如表 3 第 4 行的「恒差 6」单位陷阱：只平移截距，不影响斜率与 eφ）。

确认方式：`--all`（全部接受当前值）或 `--accept <id>`（逐条），`--note` 会写进 `meta.gate.by`。

## 思考模式必须关掉（踩过的坑）

DeepSeek 的思考（推理）模式**默认开启且 effort=high**。一旦开启，思维链会先把 `max_tokens` 吃光，`content` 回空、`finish_reason=length` —— 表现就是「识别失败：模型返回了空内容（思考 19847 字，正文 0 字）」。

- 所有模型请求统一带 `"thinking": {"type": "disabled"}`（`_post_with_thinking()`）；老模型不认这个字段会自动降级成 `reasoning_effort: "low"` 重发一次。
- 思考模式下 `temperature` 本来就不生效，已经从请求体里去掉。
- `/detect` 的 `max_tokens` 从 300 放宽到 1200（300 连标题都可能被截断）。
- 参考：DeepSeek 文档「思考模式」<https://api-docs.deepseek.com/zh-cn/guides/thinking_mode/>；同名 bug <https://github.com/deepseek-ai/DeepSeek-V3/issues/1610>。

## 用量台账

每次调模型都会：① 往控制台打一行 `[usage] tag=... in=... out=... total=...`；② 追加到 `07_流水线\projects\_debug\usage.jsonl`；③ 可通过 `GET /usage?n=20` 查最近若干条。页面在识别完成/失败时也会显示 token 数（失败的调用同样计费，所以照样显示）。

## 网站接口（bridge.py，127.0.0.1:8732）

| 端点 | 干什么 |
|---|---|
| `GET /health` | 探活：模式（mock/real）、模型、已接入实验 |
| `POST /detect` | 只看图判断是哪个实验（max_tokens 300） |
| `POST /recognize` | 读表格 → `{tables, notes, meta}`；HEIC 自动转 JPEG（长边 1600、q88，走 stdin/stdout 不落临时盘） |
| `POST /style` | **读用户以前的报告，抽风格卡**（句长/人称/连接词/段落习惯/标点/高频词组 + 硬约束「不复用连续 12 字」） |
| `POST /ping` | 真连通性测试（max_tokens 1） |
| `POST /calc` | 确定性计算（`calc_<id>`） |
| `POST /render` | 计算 → IR → docx；带 `shot_b64` 就把学习通截图贴进最后一页的 1×1 框 |
| `GET /file?path=` | 下载产物（带路径穿越校验） |

## 风格卡（style.py）

`python style.py <hw.docx> [out.json]`。只抽可量化、可校验的东西，不做主观发挥：

- 篇幅与句长（总字数、句数、平均句长、长短句占比）
- 人称（**用「我」的段落占比**，比数总字数可靠：体会段满篇我、原理段没有）
- 连接词/口语词频率、标点偏好、段首习惯、高频 2-gram
- 输出 `summary`（给人看）+ `prompt_hints`（给模型当 few-shot 约束）

注意：目前是「读进来、抽出来、存下来、界面上给你看」，**真正按风格改写正文还差一步 `/rewrite`**（要用文本模型，见「还没做」）。

## 已验证

- 与已交付报告完全一致：m = −22.09524、r = −0.998076、**eφ = 4.3854 eV**、相对误差 **−3.40 %**、u = 0.1112 eV；docx 126 段 / 5 表 / 7 图，页眉页脚正确。
- 反向测试：把 `meta.gate.confirmed` 置 false 后 `calc` 被拦下并给出修复命令。
- 稳健性对照：改用精确 1/T（不截断两位小数）得 eφ = 4.4612 eV —— 说明「表里写几位就算几位」是刻意的，不是失误。
- 三个实验都能从网页出片（`tests/smoke_render.py`，3/3）：光电效应 2520.7 KB、钨 2091.3 KB、杨氏模量 1456.8 KB，KPI 各自正确。
- 学习通截图真贴进 docx（`tests/check_p1.py` 15 项）：无截图 6 图 + 空框提示，有截图 7 图 + 文件大 103 KB，截图同时落盘 `projects/<proj>/source/shot.jpg`。
- 刷新不丢进度（`tests/check_p1_front.js` 16 项）：草稿存 localStorage（不存密钥、不存文件内容），刷新后自动恢复实验名/文件勾选/识别结果/风格摘要，可一键清空。

## 接下一个实验要改什么

1. 加 `experiments/<id>.json`（表格结构、范式、勘误、公认值、图与图注）；
2. 在 `core.py` 加 `calc_<id>()`——只做数学，输入输出都是 JSON；
3. 渲染器复用 `04_生成过程_脚本图表/build_report_<key>.py`（已支持 `PIPE_DATA/PIPE_MD/PIPE_OUT/PIPE_SHOT` 环境变量覆盖）；
4. 若范式没写过，先在本目录跑通再谈网站——**网站只是把这一套搬进浏览器**。

## 还没做（按优先级）

- ⑤ 按风格改写正文：风格卡已经抽出来了（`/style`），但正文仍来自 `content_*.md`；下一步接 `/rewrite`（文本模型 + 风格卡 + 「不得复用连续 12 字」校验）；
- ② 读图接视觉模型（`deepseek-v4-flash-vision-exp`，一张图 ≤384 tokens，需按表切图）；
- PDF：本机装不了 PDF 库，走「打印版 HTML → 浏览器打印」；
- review.html 目前只读，下一步做成可点选确认（改完直接写回 data.json）；
- 11 套讲稿里只有 3 套（photo / tungsten / young）有 `experiments/*.json` + `sections_*.py`，剩下 8 套要逐个接。

## 十一、11 套实验接入状态

| id | 讲稿 | 报告名 | 结果（示例数据，`check_all_experiments.py`） |
|---|---|---|---|
| photo | 实验 47 | 光电效应的研究 | h = 6.750×10⁻³⁴ J·s，误差 +1.88%，u = 0.906 |
| tungsten | 实验 53 | 钨的逸出功测定 | eφ = 4.385 eV，误差 −3.40%，u = 0.111 eV |
| young | 实验 24 | 用静态拉伸法测金属丝的杨氏弹性模量 | Y = 2.017×10¹¹ Pa，u/Y = 2.84% |
| linear | — | 固体线膨胀系数的测定 | α = 2.261×10⁻⁵ ℃⁻¹，误差 −1.69% |
| tension | 实验 26 | 液体表面张力系数测定 | α = 74.50 mN/m，误差 +2.85% |
| malus | 实验 8 | 验证马吕斯定律 | k = 0.979，r = 0.9998，偏差 0.81% |
| prism | 实验 21 | 用分光计测量三棱镜的折射率 | n = 1.5190，误差 +0.02% |
| light | 实验 49 | 光速测定 | c = 3.053×10⁸ m/s，误差 +1.84% |
| michelson | 实验 42 | 迈克耳孙干涉仪 | λ = 631.3 nm，误差 −0.23% |
| hfield | 实验 31 | 用霍尔效应测磁场 | B₀ = 2.250 mT，叠加偏差 0.71% |
| hall | 实验 30 | 霍尔效应及其应用 | n = 1.921×10²¹ m⁻³，R_H = 32.49 |

新增一个实验 = 只写 5 个文件（见 `EXPERIMENT_SPEC.md`），`core.py`/`bridge.py`/`ir.py`/`render_docx.py` 都不用动。

## 十二、部署（让别人也能用）

见 `06_网站方案\部署指南.md`：三种方案（局域网 ¥0 / Cloudflare Tunnel ¥0 / 云服务器 ¥30–60 月），
以及上线前必须补的三处（bridge 地址可配置、访问口令、projects 自动清理）。
其中「bridge 地址可配置」与「访问口令 `BRIDGE_TOKEN`」已经做完：
页面右上角「连接设置」可改地址与口令，`python bridge.py --host 0.0.0.0` 可对局域网开放。
