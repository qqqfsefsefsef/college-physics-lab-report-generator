# 新增一个实验：只写 5 个文件（给实现者看的契约）

> 这份文档是给「接新实验」的人（或 AI）看的。照着做，不要改 `core.py` / `bridge.py` /
> `ir.py` / `render_docx.py` 这四个公共文件——它们已经支持插件式新增。

---

## 0. 你已经有的两个样板（先读，再动手）

| 文件 | 说明 |
|---|---|
| `07_流水线\experiments\young.json` | 定义文件，字段最全 |
| `07_流水线\sections_young.py` | 分节排版，77 个 block，最干净 |
| `07_流水线\calc_photo.py` | 计算模块写法（`calc(ed, data, lsq)`） |
| `07_流水线\content\young.md` | 正文写法（9 节 `=== 名称 ===`） |
| `07_流水线\samples\make_young_synthetic.py` | 怎么造「像真的」桩数据 |

---

## 1. 你要产出的 5 个文件（全部新建，不要动别人的）

以 `<id>` 为实验短 id（见下表）：

```
07_流水线\experiments\<id>.json      # 定义：名称/公式/表格/图/KPI/勘误
07_流水线\sections_<id>.py           # 排版：把 calc 结果摆成 block 序列
07_流水线\calc_<id>.py               # 计算：calc(ed, data, lsq) -> dict
07_流水线\mock_<id>.py               # 桩数据：mock(ed) -> {'exp_id','tables','notes'}
07_流水线\content\<id>.md            # 正文：9 节，纯文本
```

## 2. 八个待接实验（id / 正式名称必须逐字一致）

正式名称要和 `06_网站方案\prototype_v2.html` 里下拉框的选项**一字不差**，否则页面认不出来。

| id | 正式名称 | 讲稿 | 页数 |
|---|---|---|---|
| `linear` | 固体线膨胀系数的测定 | `02_实验讲稿\固体线膨胀系数的测定\1..5.png` | 5 |
| `tension` | 液体表面张力系数测定 | `02_实验讲稿\液体表面张力系数测定\1 (1).png` … | 6 |
| `malus` | 验证马吕斯定律 | `02_实验讲稿\验证马吕斯定律\1..4.png` | 4 |
| `prism` | 用分光计测量三棱镜的折射率 | `02_实验讲稿\用分光计测量三棱镜的折射率\` | 9 |
| `light` | 光速测定 | `02_实验讲稿\光速测定\1..4.png` | 4 |
| `michelson` | 迈克耳孙干涉仪 | `02_实验讲稿\迈克耳孙干涉仪\` | 6 |
| `hfield` | 用霍尔效应测磁场 | `02_实验讲稿\用霍尔效应测磁场\` | 7 |
| `hall` | 霍尔效应及其应用 | `02_实验讲稿\霍尔效应及其应用\1..9.png` | 9 |

> 注意：`hfield`（实验 31，测磁场、验叠加）和 `hall`（实验 30，对称测量法、载流子浓度）
> 是**两个不同实验**，别合并。
> 有些目录里首图叫 `1 (1).png`（浏览器重复下载），按实际文件名读。

---

## 3. `experiments\<id>.json` 字段

照抄 `young.json` 改。必填：

```jsonc
{
  "id": "linear",
  "no": "实验 XX",                       // 讲稿标题里的编号；没有就写 ""
  "name": "固体线膨胀系数的测定",          // 必须与下拉框一致
  "calc": "linear",                      // calc_<id>.py
  "checks": "linear",                    // checks 可省；省了走通用检查
  "renderer": "ir",                      // 固定写 "ir"
  "content": "07_流水线\\content\\linear.md",
  "footer": "固体线膨胀系数",             // 页脚，短一点
  "accepted": 1.0,                       // 公认值（可空）
  "paradigm": "line_fit",                // 处理范式，仅作说明
  "objectives": ["…", "…", "…"],         // 实验目的，直接取自讲稿
  "formulas": {                          // 正文里用 [[F1]] 引用
    "F1": "L = L₀(1 + α*t*)"            // 迷你标记：*斜体* _{下标} ^{上标}
  },
  "tables": {                            // 表规格：tid -> 表头/列数（给读图模型看的）
    "t1": {"title": "表1 L~t 数据", "cols": ["t/℃", "L/mm"], "rows": 8}
  },
  "figures": [],                         // 需要插的图片（放 04_生成过程_脚本图表，可空）
  "kpi": [                               // 结果页三个大数字，键名 = calc 里 result 的键
    {"label": "线膨胀系数 α / 10⁻⁵ ℃⁻¹", "key": "alpha", "scale": 1e5, "digits": 3},
    {"label": "与公认值的相对误差", "key": "rel_err_pct", "digits": 2, "signed": true, "suffix": "%"},
    {"label": "不确定度 u(α) / 10⁻⁵ ℃⁻¹", "key": "u_alpha", "scale": 1e5, "digits": 3}
  ],
  "errata": ["讲稿第 3 页式(4) 编号重复，正文按式(5) 引用"]   // 讲义自身的问题，有就记
}
```

## 4. `calc_<id>.py` 契约

```python
def calc(ed, data, lsq):
    """data['tables'] 是 {tid: {'cells': 二维数组}}，cells 第一行通常是表头。
    返回：{'t1': {...给 sections 用的干净数据...}, 'result': {...给 KPI/正文用...}}
    'result' 里必须出现 experiments/<id>.json 的 kpi 里所有 key。
    """
    cells = data['tables']['t1']['cells']
    ...
    return {'t1': {...}, 'result': {'alpha': ..., 'u_alpha': ..., 'rel_err_pct': ...}}
```

硬要求：

- **不许 import 任何第三方库**（只用 `math` / `json` / 标准库）。
- 数字一律从 `cells` 解析，用 `float()` 容错（`''`、`'−0.5'`（U+2212）都要能转）。
- 不确定度：能算就算（A 类用贝塞尔，B 类按仪器误差限），算不了就给出合理估计并写进 errata。
- 中间结果保留 1–2 位多余数字，最终结果按有效数字规则。

## 5. `mock_<id>.py` 契约

```python
def mock(ed):
    return {
        'exp_id': ed['id'],
        'tables': {'t1': {'cells': [[...], ...]}},   # 与讲稿表格列一致
        'notes': [                                    # 至少一条「可纠正的问题」
            {'table': 't1', 'row': 2, 'col': 1,
             'where': '表1 · 第 3 次 · L 那一格',
             'current': '12.34', 'candidates': ['12.34', '12.36'],
             'why': '笔迹压线，看着像 4 也像 6'}
        ],
    }
```

要求：数据要**物理上自洽**（能算出合理的公认值，误差个位数百分比），并故意留 1–2 处
像真学生会写错的地方；`row/col` 是 `cells` 的下标（0 开始，含表头行）。

## 6. `sections_<id>.py` 契约

```python
def build(exp, calc, md):
    blocks = []
    blocks.append({'t': 'sect', 'name': '实验目的', 'pct': '10%'})
    ...
    return blocks
```

可用 block 类型（`render_docx.render` 认识这些）：

| type | 字段 | 用途 |
|---|---|---|
| `sect` | `name`, `pct`, `note`(红字说明，可选) | 【实验目的】10% |
| `para` | `text`, `indent`(默认 True), `bold`, `center` | 正文段（首行缩进 2 字符） |
| `note` | `text` | 红字说明 |
| `formula` | `expr`（迷你标记，见下） | 独立成行的公式 |
| `caption` | `text`, `bold` | 表题（在表**上方**）／图注（在**下方**由 figure 负责） |
| `table` | `rows`, `widths`(twips，**合计 8300**), `header`(1), `merges`=[(r0,c0,r1,c1)], `borderless` | 表格 |
| `figure` | `path`, `width_cm`, `caption` | 插图（图在上、图注在下） |
| `shot` | `path`, `width_cm`, `row_h` | 超星截图粘贴框（固定放最后一节） |
| `heading` | `text`, `center` | 小标题 |
| `pagebreak` | — | 分页 |

公式迷你标记：`*x*` 斜体、`_{s}` 下标、`^{2}` 上标。例：`"*Y* = 8*FLD* / (π*d*²*K*N̄)"`。

正文 `md` 来自 `content/<id>.md`，结构是：

```
=== 原理1 ===
……段落……

[[F1]]

……段落……
```

`ir.py` 会把 `=== 名称 ===` 切成小节、把独占一行的 `[[F1]]` 换成 `formulas["F1"]` 的公式块。
**节名固定用**：`原理1` `原理2` `原理3` `原理4` `仪器` `步骤` `数据说明` `体会` `思考题`。
节顺序由 `sections_<id>.py` 的 `build()` 决定，md 里只负责提供文字。

## 7. `content\<id>.md` 契约

- 9 个 `=== 名称 ===` 段，段间空行，纯文本（**不要 Markdown 记号**：`#`、`*`、`-`、`>`）。
- 字数（去空白）：原理合计 2200–3200；仪器 250–400；步骤 500–800；数据说明 400–600；
  体会 ≥700（第一人称「我」）；思考题 500–700（题目 + 解答，每题解答 80–160 字）。
- **不写具体测量数字**（数字来自 calc，由 `sections_<id>.py` 注入）。
- 中文全角标点；数字与单位之间留空格；`A_s` `U_s` 这类下标一律直接写字母加下划线，渲染器会转真下标。
- 每节都要「言之有物」：来自讲稿的公式和步骤，别写通用套话。

## 8. 自测（必须跑到全绿再交）

```powershell
$py='C:\Users\lidey\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
& $py 'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\tests\check_all_experiments.py' linear
```

期望输出形如：

```
[OK] linear     blocks= 82 docx= 1460.3 KB  alpha=1.234 rel_err_pct=-2.31 u_alpha=0.087
全部通过
```

同时手工看一眼产物：`07_流水线\projects\_p0test\linear.docx`（用 Word 打开或看大小是否合理，
一般 1.2–3 MB；如果只有几百 KB，多半是表格/图没插进去）。

## 9. 硬规则（违反会打回）

1. **只新建上面 5 个文件**；不改 `core.py` / `bridge.py` / `ir.py` / `render_docx.py` /
   别人的 `sections_*` `calc_*` `mock_*` `experiments/*.json`。
2. 表格 `widths` 合计必须 **8300** twips（A4 正文宽），否则左边会歪。
3. `result` 里 kpi 需要的键**一个都不能缺**，缺了页面显示「—」。
4. 负号用 U+2212 `−`，不要用 ASCII `-`（页面与 docx 都按印刷体处理）。
5. 讲稿与常识不一致时以讲稿为准，但**在 `errata` 里记一条**；真错了才改，改了就写清楚。
6. 不要编造型号、不要编造实验台号、不要在正文里写死测量值。
7. 交回时列清：五个文件路径、`check_all_experiments.py <id>` 的输出、你记了几条 errata。
