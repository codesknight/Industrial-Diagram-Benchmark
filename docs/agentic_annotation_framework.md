# Agentic Annotation Framework for Topology Panel v1.5

日期：2026-07-10

## 目标

当前 Topology Panel v1 只有 14 条 clean baseline，只适合作为 pilot benchmark。为了向 CCF-B 级别 benchmark 标准推进，下一阶段目标是构建 Topology Panel v1.5：

- 从 14 条扩展到 100-150 条 clean single-panel topology samples。
- 尽量减少人工低价值筛查。
- 让多个视觉模型先做独立判断，再由 consensus 自动仲裁。
- 人工只处理模型冲突、低置信和高风险样本。

核心原则：

> AI 能做的低价值重复判断交给 AI；人只处理高不确定、高影响、高争议样本。

## 智能体角色

当前框架默认使用 3 个 vision agents：

| agent | env key | model env | default base URL |
| --- | --- | --- | --- |
| Doubao | `DOUBAO_API_KEY` | `DOUBAO_VISION_MODEL` | `https://ark.cn-beijing.volces.com/api/v3` |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_VISION_MODEL` | `https://api.deepseek.com` |
| Zhipu | `ZHIPU_API_KEY` | `ZHIPU_VISION_MODEL` | `https://open.bigmodel.cn/api/paas/v4` |

脚本不会打印 API key。

## 标注标签

agent 必须从以下标签中选择一个：

| label | 含义 | 是否可进入 v1.5 |
| --- | --- | --- |
| `accept_clean_topology` | 单一、清晰、无明显阻塞问题的拓扑目标图 | 可进入候选 |
| `reject_multi_subfigure` | 一张图包含多个独立子图或多个图框 | 排除 |
| `reject_visible_watermark` | 图像内容可见明显水印/图库/网站标记 | 排除 |
| `reject_bad_geometry` | 空白、损坏、几何异常、不可读 | 排除 |
| `reject_not_topology` | 平面布置、表格、图例、标题页等非拓扑目标 | 排除 |
| `needs_terminal_anchor` | 线拓扑可用，但端子/符号锚点不足 | v1.5 暂缓，进入改进池 |
| `needs_graph_repair` | 是拓扑目标，但当前 graph 有碎裂/过连接等问题 | v1.5 暂缓，进入改进池 |
| `uncertain` | 证据不足或冲突 | 人工复核 |

## 自动仲裁规则

`scripts/run_agentic_panel_annotation.py` 使用以下规则：

- `auto_accept`
  - 至少 2 个 agent 投 `accept_clean_topology`。
  - 该标签平均 confidence >= 0.80。
  - 没有任何 hard reject vote。
- `auto_reject`
  - 至少 2 个 agent 投同一个 hard reject label。
  - 平均 confidence >= 0.75。
- `auto_defer_improvement`
  - 至少 2 个 agent 投 `needs_terminal_anchor` 或 `needs_graph_repair`。
  - 平均 confidence >= 0.75。
- `human_review`
  - 其他所有情况。

hard reject labels：

```text
reject_multi_subfigure
reject_visible_watermark
reject_bad_geometry
reject_not_topology
```

## 推荐流程

### 1. 生成 v1.5 candidate manifest

```powershell
python scripts/build_topology_panel_v1_5_candidate_manifest.py
```

输出：

```text
data_index/topology_panel_v1_5_candidate_manifest.csv
data_index/topology_panel_v1_5_candidate_summary.json
data_index/topology_panel_v1_5_candidate_report.md
```

### 2. 小批量 dry-run 验证框架

```powershell
python scripts/run_agentic_panel_annotation.py --dry-run --limit 20
python scripts/build_agentic_annotation_review_html.py
```

### 3. 小批量真实 API 标注

建议先跑 10-20 条，检查三个 provider 是否都支持 image input：

```powershell
python scripts/run_agentic_panel_annotation.py --limit 20
python scripts/build_agentic_annotation_review_html.py
```

### 4. 扩大到完整候选池

```powershell
python scripts/run_agentic_panel_annotation.py
python scripts/build_agentic_annotation_review_html.py
```

### 5. 人工只审 conflict/uncertain

打开：

```text
data_index/topology_panel_v1_5_agentic_annotation_review.html
```

该 HTML 默认只展示 `human_review` 样本，并可导出人工复核 CSV。

## 产物解释

| file | 用途 |
| --- | --- |
| `*_agent_outputs.csv` | 每个 agent 的独立判断、置信度、理由 |
| `*_consensus.csv` | panel 级共识标签与决策 |
| `*_summary.json` | 统计信息 |
| `*_report.md` | 人类可读报告 |
| `*_review.html` | 仅冲突/低置信样本的快速审核表 |

## v1.5 进入标准

一个样本进入 Topology Panel v1.5 clean benchmark，必须满足：

1. consensus decision 为 `auto_accept`，或人工复核后确认为 clean。
2. 图像是单一 panel，不含多个独立子图。
3. 图像内容无明显可见水印。
4. 是 wiring / terminal / control / connection topology target。
5. 几何和拓扑 JSON 文件存在且可读。
6. node/edge/net count 为正。
7. 后续 evaluator 能正常处理。

## CCF-B 级升级目标

v1.5 不应只追求数量，还要追求可复用性：

- 数据版本冻结。
- 标注协议公开。
- agent 输出和人工覆盖路径可审计。
- evaluator 一条命令可复现。
- baseline 至少包含 rule-based、VLM、hybrid 三类。
- per-sample error details 保留。
- Hugging Face Dataset 与 GitHub README 同步。

