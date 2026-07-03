# Industrial Diagram Benchmark：面向工业接线图理解与 CAD 重建的研究路线

## 1. 项目定位

本项目旨在构建一套面向工业电路图纸、接线图、控制柜图、PLC 图和配电图的结构化理解与生成框架。

核心目标不是单纯完成图像识别，而是建立一条完整的工程闭环：

```text
工业 DWG / DXF / PNG
        │
        ▼
DXF Parser / Image Parser
        │
        ▼
Geometry JSON
        │
        ▼
Topology Graph
        │
        ▼
VQA Dataset
        │
        ▼
Industrial Diagram Benchmark
        │
        ▼
Tool-Augmented VLM
        │
        ▼
CAD Agent
        │
        ▼
DXF Generation / Diagram Modification / Rule Verification
```

本路线可以作为以下研究方向的基础：

- 工业图纸理解 Benchmark
- 电气接线图 VQA 数据集
- CAD 图纸结构化解析
- 图纸拓扑关系抽取
- Tool-Augmented VLM
- CAD Agent
- 图纸生成与自动校验

---

## 2. 推荐论文题目

### 英文题目

```text
IndustrialDiagram-Bench: A Geometry-Topology Benchmark for Industrial Wiring Diagram Understanding and CAD Reconstruction
```

### 中文题目

```text
面向工业接线图理解与 CAD 重建的几何—拓扑结构化 Benchmark
```

该题目相比普通“电路图 VQA”更有研究价值，因为它覆盖了：

- 工业图纸
- 结构化表示
- 拓扑理解
- 自动问答
- CAD 重建
- 工具增强
- Agent 闭环

---

## 3. 总体研究目标

本研究希望解决以下问题：

1. 如何将复杂工业 DWG / DXF 图纸转换为可被模型理解的结构化表示？
2. 如何从图纸中抽取元件、文本、端口、连线和拓扑关系？
3. 如何基于拓扑图自动构造高质量 VQA 数据？
4. 如何设计一个覆盖检测、解析、推理、校验和 CAD 重建的 Benchmark？
5. 如何利用工具增强 VLM，减少图纸理解中的幻觉和连接错误？
6. 如何进一步实现自然语言到 CAD 图纸生成、修改与校验？

---

## 4. 数据来源与输入格式

### 4.1 图纸类型

建议优先关注以下工业图纸：

| 图纸类型 | 说明 | 研究价值 |
|---|---|---|
| 电气原理图 | 包含继电器、开关、电源、接地等元件 | 适合元件识别与拓扑推理 |
| 接线图 | 包含端子、线号、设备编号和连接关系 | 最贴近工业应用 |
| PLC 图 | 包含输入输出模块、地址、信号线 | 适合结构化问答 |
| 配电图 | 包含断路器、母线、负载、接地 | 适合工程规则推理 |
| 控制柜图 | 包含柜体、端子排、线缆、元件布局 | 适合 CAD Agent 场景 |

### 4.2 数据格式

可支持以下输入格式：

```text
DWG / DXF / PDF / PNG
```

其中，DXF 是最关键的中间格式，因为它可被程序直接解析。

推荐数据转换流程：

```text
DWG
 ↓
ODA Converter / LibreDWG / AutoCAD API
 ↓
DXF
 ↓
Python Parser
 ↓
JSON / PNG / Graph
```

---

## 5. DXF Parser：图纸几何解析

### 5.1 解析目标

DXF Parser 的目标是从 CAD 文件中提取原始图元，包括：

| DXF Entity | 含义 |
|---|---|
| LINE | 直线 |
| LWPOLYLINE | 多段线 |
| CIRCLE | 圆 |
| ARC | 圆弧 |
| TEXT / MTEXT | 文本 |
| INSERT | 块引用，常用于元件符号 |
| BLOCK | 元件模板 |
| HATCH | 填充 |
| DIMENSION | 尺寸标注 |

### 5.2 第一阶段输出：Raw Geometry JSON

第一阶段不追求语义理解，只追求几何保真。

示例：

```json
{
  "drawing_id": "sample_001",
  "entities": [
    {
      "id": "line_001",
      "type": "LINE",
      "layer": "WIRE",
      "start": [120.5, 300.0],
      "end": [240.5, 300.0]
    },
    {
      "id": "text_001",
      "type": "TEXT",
      "layer": "LABEL",
      "text": "K1",
      "position": [130.0, 320.0],
      "height": 3.5
    },
    {
      "id": "block_001",
      "type": "INSERT",
      "name": "RELAY",
      "position": [200.0, 280.0],
      "rotation": 0
    }
  ]
}
```

该表示称为：

```text
Geometry JSON
```

它的作用是将 CAD 图纸转换为模型可读、程序可处理、可校验的数据结构。

---

## 6. Geometry JSON：标准结构表示

### 6.1 为什么需要 JSON 中间表示？

直接让 VLM 读取 DWG / DXF 很困难，原因包括：

- CAD 文件格式复杂；
- 图元数量巨大；
- 存在大量冗余信息；
- 模型难以直接理解坐标、图层、块引用；
- 不利于训练、评估和自动校验。

因此需要设计中间表示：

```text
DXF / DWG
 ↓
Geometry JSON
 ↓
Topology Graph
 ↓
VLM / Agent
```

JSON 的优势：

| 优势 | 说明 |
|---|---|
| 可读 | 人和模型都能理解 |
| 可控 | 可以约束字段 |
| 可校验 | 可以写 Validator |
| 可训练 | 可以构建 image-to-JSON 数据对 |
| 可还原 | JSON 可以再转回 DXF |

### 6.2 三层 JSON 设计

为了避免 JSON 过长，建议采用三层结构：

```text
Raw Geometry JSON
    ↓
Normalized Geometry JSON
    ↓
Semantic Diagram JSON
```

#### 6.2.1 Raw Geometry JSON

保留所有原始图元。

```json
{
  "type": "LINE",
  "start": [100, 200],
  "end": [300, 200],
  "layer": "0"
}
```

#### 6.2.2 Normalized Geometry JSON

去掉冗余字段，只保留标准化后的必要信息。

```json
{
  "id": "wire_001",
  "primitive": "line",
  "p1": [100, 200],
  "p2": [300, 200]
}
```

#### 6.2.3 Semantic Diagram JSON

加入元件、端口、连线和文本语义。

```json
{
  "components": [
    {
      "id": "K1",
      "type": "relay",
      "bbox": [180, 250, 240, 310],
      "ports": ["K1_A1", "K1_A2"]
    }
  ],
  "wires": [
    {
      "id": "wire_001",
      "from": "K1_A1",
      "to": "terminal_X1_1"
    }
  ]
}
```

Semantic Diagram JSON 是后续训练模型、构建 Benchmark 和生成 CAD 的核心表示。

---

## 7. Topology Graph：连接关系图

### 7.1 为什么需要拓扑图？

工业图纸的本质不是图片，而是结构关系。

模型真正需要理解的是：

```text
谁和谁连接？
信号从哪里来？
经过哪些元件？
最后到哪里？
是否满足工程规则？
```

因此需要从 Geometry JSON 构建 Topology Graph。

### 7.2 图结构定义

可以定义为：

```text
G = (V, E)
```

其中：

| 符号 | 含义 |
|---|---|
| V | 节点，包括元件、端子、端口、文本、连接点 |
| E | 边，包括连线关系、标签关系、包含关系、几何关系 |
| 属性 | 坐标、类型、编号、层名、文本、方向等 |

### 7.3 节点示例

```json
{
  "nodes": [
    {
      "id": "K1",
      "type": "relay",
      "label": "K1",
      "bbox": [100, 200, 160, 260]
    },
    {
      "id": "X1_1",
      "type": "terminal",
      "label": "X1:1",
      "bbox": [300, 200, 320, 220]
    }
  ]
}
```

### 7.4 边示例

```json
{
  "edges": [
    {
      "source": "K1_A1",
      "target": "X1_1",
      "type": "wire",
      "wire_id": "W001"
    },
    {
      "source": "text_K1",
      "target": "K1",
      "type": "label_of"
    }
  ]
}
```

### 7.5 关系类型

至少需要三类关系：

| 关系类型 | 示例 | 用途 |
|---|---|---|
| 几何关系 | A 在 B 左侧、A 与 B 相交 | 定位与布局理解 |
| 连接关系 | K1_A1 连到 X1_1 | 电路拓扑理解 |
| 语义关系 | 文本 K1 是继电器标签 | OCR 与元件绑定 |

---

## 8. VQA Dataset：结构化问答数据集

### 8.1 为什么需要 VQA？

Benchmark 不能只评估检测框，还需要评估模型是否真正理解图纸。

工业图纸中常见问题包括：

```text
K1 连接到了哪个端子？
X1:3 的信号来自哪里？
这个回路经过了哪些元件？
图中有几个继电器？
哪个设备接地？
是否存在未连接端口？
```

这些问题更能体现模型的结构理解能力。

### 8.2 VQA 类型设计

| 类型 | 示例问题 | 答案示例 |
|---|---|---|
| Counting | 图中有几个继电器？ | 3 |
| Recognition | K1 是什么元件？ | 继电器 |
| Localization | X1:1 在图纸哪个区域？ | 右上角 |
| Connection | K1_A1 连到哪里？ | X1:1 |
| Path Reasoning | 从 S1 到 M1 经过哪些元件？ | S1 → K1 → M1 |
| Fault Check | 是否存在未连接端口？ | 是，K2_A2 |
| Text-Grounding | 文本 “24V” 标注的是哪个节点？ | 电源节点 VCC |
| Rule Reasoning | 该回路是否接地？ | 是 |

### 8.3 基于 Graph 自动生成 QA

如果拓扑图中存在如下连接：

```json
{
  "source": "K1_A1",
  "target": "X1_1",
  "type": "wire"
}
```

可以自动生成 QA：

```json
{
  "question": "K1 的 A1 端口连接到哪里？",
  "answer": "X1 的 1 号端子",
  "evidence": ["K1_A1", "X1_1", "wire_001"],
  "reasoning_type": "connection"
}
```

建议每个 QA 样本保留 evidence 字段，方便后续评估模型是否真正基于图纸证据推理。

---

## 9. Industrial Diagram Benchmark 设计

### 9.1 Benchmark 总体任务层级

建议将 Benchmark 设计为多层级任务：

```text
Level 1: Symbol Detection
Level 2: Text Recognition
Level 3: Port Detection
Level 4: Wire Parsing
Level 5: Topology Extraction
Level 6: JSON Generation
Level 7: Diagram VQA
Level 8: Rule Verification
Level 9: CAD Reconstruction
```

### 9.2 任务、输入、输出与指标

| 层级 | 任务 | 输入 | 输出 | 指标 |
|---|---|---|---|---|
| L1 | 元件检测 | PNG | bbox + class | mAP |
| L2 | OCR | PNG | text + bbox | CER / WER |
| L3 | 端口识别 | PNG | port bbox | AP |
| L4 | 线缆解析 | PNG | wire polyline | IoU / F1 |
| L5 | 拓扑抽取 | PNG / JSON | graph | Graph F1 |
| L6 | JSON 生成 | PNG | semantic JSON | JSON Edit Distance |
| L7 | 图纸问答 | PNG + Question | answer | Accuracy / F1 |
| L8 | 规则校验 | JSON / Graph | pass / fail | Success Rate |
| L9 | CAD 重建 | JSON / Prompt | DXF | CAD Consistency |

### 9.3 Benchmark 的创新性

现有电路图 Benchmark 多集中在以下方向：

- 元件检测；
- OCR；
- Netlist 转换；
- 普通电路问答；
- 学科题目推理。

但工业接线图仍缺少覆盖以下能力的 Benchmark：

```text
几何解析
拓扑理解
结构化问答
工程规则校验
CAD 重建
工具增强推理
```

因此，本项目的创新点在于：

```text
不是只看图，而是理解图纸结构；
不是只回答问题，而是能还原 CAD；
不是只做 VQA，而是加入规则校验和工具调用；
不是只做感知，而是形成图纸理解与生成闭环。
```

---

## 10. Tool-Augmented VLM 框架

### 10.1 为什么需要工具增强？

纯 VLM 在工业图纸理解中容易出现以下问题：

| 问题 | 表现 |
|---|---|
| OCR 错误 | 线号、端子号、元件编号识别错误 |
| 连接幻觉 | 将视觉上接近但未连接的线误判为连接 |
| 坐标不准 | 无法精确定位端口或连线交点 |
| 多跳推理不稳定 | 路径追踪和回路分析容易出错 |
| JSON 不合法 | 输出字段缺失、格式错误、坐标异常 |
| CAD 不可用 | 生成结果无法渲染或不符合工程规则 |

因此需要将 VLM 与外部工具结合。

### 10.2 可调用工具

| 工具 | 作用 |
|---|---|
| DXF Parser | 读取 CAD 图元 |
| OCR Tool | 识别文本和编号 |
| Detector | 检测元件和符号 |
| Port Detector | 定位端口 |
| Wire Tracer | 追踪连线 |
| Graph Builder | 构建拓扑图 |
| Validator | 检查 JSON 合法性 |
| Rule Engine | 检查工程规则 |
| DXF Renderer | 将 JSON 渲染回 CAD |
| Visual Comparator | 比较原图和重建图 |

### 10.3 Tool-Augmented 推理流程

示例问题：

```text
K1 的 A1 端口连接到哪里？
```

推理流程：

```text
1. VLM 调用 Detector 找到 K1
2. 调用 Port Detector 找到 A1
3. 调用 Wire Tracer 追踪连线
4. 调用 Graph Builder 查询拓扑关系
5. 调用 Validator 检查答案是否与 graph 一致
6. 返回答案
```

### 10.4 Agent Trajectory 数据格式

工具调用过程可以保存为训练数据：

```json
{
  "question": "K1 的 A1 端口连接到哪里？",
  "trajectory": [
    {
      "tool": "detect_component",
      "input": "K1",
      "output": "component_id=K1"
    },
    {
      "tool": "find_port",
      "input": "K1_A1",
      "output": "port_id=K1_A1"
    },
    {
      "tool": "trace_wire",
      "input": "K1_A1",
      "output": "X1_1"
    }
  ],
  "answer": "K1 的 A1 端口连接到 X1 的 1 号端子。"
}
```

这类数据可以用于训练 CAD / Diagram Agent。

---

## 11. CAD Agent：生成、修改与校验

### 11.1 CAD Agent 能力

| 能力 | 示例 |
|---|---|
| 读取图纸 | 解析这张接线图 |
| 查询图纸 | K1 接到哪里？ |
| 修改图纸 | 把 K1 改成 K2 |
| 新增元件 | 增加一个断路器 QF1 |
| 自动布线 | 把 QF1 接到 M1 |
| 生成 DXF | 根据描述生成接线图 |
| 校验规则 | 检查是否有悬空端口 |
| 对比图纸 | 新旧图纸有哪些变化？ |

### 11.2 CAD 生成流程

```text
用户自然语言
 ↓
LLM 生成 Semantic JSON
 ↓
Validator 检查 JSON 合法性
 ↓
Rule Engine 检查工程规则
 ↓
JSON-to-DXF
 ↓
Renderer 渲染图纸
 ↓
Visual Comparator 比较结果
```

### 11.3 示例：文本生成接线图

用户输入：

```text
生成一个 24V 控制回路：
电源正极连接急停按钮 S1，
再连接继电器 K1 线圈 A1，
K1 的 A2 接 0V。
```

模型输出 Semantic JSON：

```json
{
  "components": [
    {
      "id": "PSU1",
      "type": "power_supply",
      "ports": ["24V", "0V"]
    },
    {
      "id": "S1",
      "type": "emergency_stop",
      "ports": ["in", "out"]
    },
    {
      "id": "K1",
      "type": "relay_coil",
      "ports": ["A1", "A2"]
    }
  ],
  "connections": [
    ["PSU1.24V", "S1.in"],
    ["S1.out", "K1.A1"],
    ["K1.A2", "PSU1.0V"]
  ]
}
```

该 JSON 经过 Validator 和 Rule Engine 检查后，再转换为 DXF 图纸。

---

## 12. 阶段性实施路线

### 阶段一：DXF 解析

目标：

```text
DXF → Geometry JSON
```

主要任务：

1. 使用 `ezdxf` 解析 LINE / TEXT / INSERT / LWPOLYLINE；
2. 统一坐标系统；
3. 提取图层、文本、块引用信息；
4. 输出 Raw Geometry JSON；
5. 将 DXF 渲染为 PNG。

---

### 阶段二：语义归一化

目标：

```text
Geometry JSON → Semantic Diagram JSON
```

主要任务：

1. 识别 block 对应的元件类别；
2. 绑定 text 与 component；
3. 识别 wire；
4. 识别 port；
5. 建立 components / ports / wires / labels 四类核心对象。

---

### 阶段三：拓扑构建

目标：

```text
Semantic Diagram JSON → Topology Graph
```

主要任务：

1. 判断线段之间是否连接；
2. 判断线段是否连接到端口；
3. 合并同一电气网络 net；
4. 构建 NetworkX 图；
5. 输出 graph JSON。

---

### 阶段四：VQA 自动生成

目标：

```text
Topology Graph → QA Dataset
```

主要任务：

1. 生成 Counting QA；
2. 生成 Component Recognition QA；
3. 生成 Connection QA；
4. 生成 Path Reasoning QA；
5. 生成 Rule Verification QA；
6. 保存 answer 与 evidence。

---

### 阶段五：Benchmark 设计

目标：

```text
Industrial Diagram Benchmark
```

主要任务：

1. 定义多层级任务；
2. 定义评估指标；
3. 划分训练集、验证集、测试集；
4. 测试 GPT-4o、Qwen-VL、InternVL、LLaVA 等模型；
5. 分析纯 VLM 在图纸理解中的失败模式。

---

### 阶段六：Tool-Augmented VLM

目标：

```text
VLM + CAD Tools
```

主要任务：

1. 封装工具 API；
2. 设计工具调用轨迹；
3. 比较纯 VLM 与 Tool-VLM；
4. 做消融实验；
5. 分析工具增强对 OCR、连接推理和路径推理的提升。

---

### 阶段七：CAD Agent

目标：

```text
自然语言 / 图像 → JSON → DXF
```

主要任务：

1. 实现 JSON-to-DXF；
2. 实现 Validator；
3. 实现 Rule Engine；
4. 实现 CAD Reconstruction 评估；
5. 支持图纸生成、修改、校验和对比。

---

## 13. 预期论文贡献

### Contribution 1：几何—拓扑中间表示

提出一种面向工业图纸的结构化表示：

```text
Geometry JSON + Topology Graph + Semantic Labels
```

该表示同时适合：

- 模型训练；
- 图纸解析；
- 拓扑推理；
- CAD 重建；
- 自动校验。

---

### Contribution 2：工业接线图 Benchmark

构建一个多层级 Benchmark，覆盖：

```text
Detection
Parsing
Topology
VQA
Rule Verification
CAD Reconstruction
```

相比已有电路图数据集，该 Benchmark 更贴近工业工程图纸场景。

---

### Contribution 3：自动数据生成 Pipeline

从已有 DXF 自动生成：

```text
PNG
Geometry JSON
Topology Graph
QA Pairs
CAD Reconstruction Target
```

该流程可以大幅降低人工标注成本。

---

### Contribution 4：Tool-Augmented VLM

提出工具增强框架：

```text
VLM + CAD Parser + Graph Tool + Validator + Renderer
```

用于减少幻觉，提高结构推理能力和工程可靠性。

---

### Contribution 5：CAD Agent 闭环

最终实现：

```text
理解图纸
回答问题
修改图纸
生成图纸
校验图纸
```

这使 Benchmark 不再停留在静态问答，而是进入真实工程应用流程。

---

## 14. 推荐项目目录结构

```text
IndustrialDiagram-Bench/
├── README.md
├── data/
│   ├── raw_dxf/
│   ├── raw_png/
│   ├── geometry_json/
│   ├── semantic_json/
│   ├── topology_graph/
│   └── vqa/
├── tools/
│   ├── dxf_parser.py
│   ├── dxf_renderer.py
│   ├── json_to_dxf.py
│   ├── graph_builder.py
│   ├── validator.py
│   └── rule_engine.py
├── benchmark/
│   ├── detection_eval.py
│   ├── ocr_eval.py
│   ├── graph_eval.py
│   ├── json_eval.py
│   ├── vqa_eval.py
│   └── cad_eval.py
├── agent/
│   ├── tools_api.py
│   ├── tool_trajectory.py
│   └── cad_agent.py
├── configs/
│   ├── dataset.yaml
│   └── benchmark.yaml
├── scripts/
│   ├── build_geometry_json.py
│   ├── build_topology_graph.py
│   ├── generate_vqa.py
│   └── run_benchmark.py
└── docs/
    ├── annotation_guideline.md
    ├── data_format.md
    └── evaluation_protocol.md
```

---

## 15. 最小可行版本 MVP

建议先做一个最小可行版本，不要一开始做太大。

### MVP 目标

```text
DXF → JSON → Graph → QA → Evaluation
```

### MVP 数据规模

| 数据 | 数量建议 |
|---|---|
| DXF 图纸 | 100 张 |
| PNG 渲染图 | 100 张 |
| Semantic JSON | 100 份 |
| Topology Graph | 100 份 |
| QA 样本 | 1000 - 3000 条 |

### MVP 任务

先完成四个任务即可：

1. 元件识别；
2. 连线关系抽取；
3. 拓扑问答；
4. JSON-to-DXF 重建。

### MVP 指标

| 任务 | 指标 |
|---|---|
| 元件识别 | mAP / Accuracy |
| 连线抽取 | Graph F1 |
| 问答 | Accuracy |
| CAD 重建 | JSON Edit Distance / Render Similarity |

---

## 16. 后续扩展方向

后续可以继续扩展到：

1. 多页图纸理解；
2. 端子排跨页连接；
3. 图纸版本对比；
4. 工程规则校验；
5. PLC 地址自动识别；
6. 电气知识图谱；
7. Agent 自动修改图纸；
8. 多模态 CAD Copilot；
9. 工业图纸检索；
10. 图纸到施工说明自动生成。

---

## 17. 一句话总结

本项目的核心思想是：

```text
将工业接线图从“图片理解问题”转化为“几何—拓扑—语义结构化建模问题”，
再通过 Tool-Augmented VLM 和 CAD Agent 实现图纸理解、问答、生成、修改与校验的完整闭环。
```
