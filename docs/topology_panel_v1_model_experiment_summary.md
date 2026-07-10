# Topology Panel v1 模型实验方法总结

日期：2026-07-10

## 1. 实验背景

Topology Panel v1 baseline 固定为 14 条人工确认可用于拓扑任务的 panel 样本。评测协议使用 `docs/topology_graph_eval_protocol_v1.md`，核心指标包括 prediction graph valid rate、node_count MAE、edge_count MAE、net_count MAE，以及 per-sample details/errors CSV。

本阶段目标不是直接完成完整 topology graph reconstruction，而是先建立真实视觉模型在工业图纸拓扑计数任务上的可复现实验链路，并逐步优化 prompt 与 image input。

## 2. 方法演进

### 2.1 Doubao v1：真实模型接入

Doubao v1 完成了 14 条 baseline 的首次真实模型接入。模型输出主要是 count-level 结果，经 adapter 转成 evaluator 可接受的 synthetic graph。

- prediction rows：14
- prediction valid rate：0.357143
- node MAE：500.857143
- edge MAE：828.357143
- net MAE：3.571429
- 主要问题：模型频繁返回 `unreadable` / `uncertain`

### 2.2 Prompt v2：修正过度不确定

Prompt v2 要求可读工业图纸优先输出 `status=ok`，不要轻易返回不可读。

- prediction valid rate：1.0
- node MAE：409.285714
- edge MAE：737.357143
- net MAE：16.357143
- 结论：status 行为显著改善，但 net_count 被严重高估

### 2.3 Prompt v3：修正 net_count 定义

Prompt v3 明确 `net_count = topology graph 连通分量数量`，不等于功能块、端子排、线束组或页面区域数量。

- prediction valid rate：1.0
- node MAE：394.642857
- edge MAE：715.642857
- net MAE：0.857143
- 结论：v3 是当前最佳 prompt，后续不再优先调 prompt

### 2.4 1024 整图输入：验证分辨率假设

固定 prompt v3，将整图输入从 512 提高到 1024。

- node MAE：399.571429
- edge MAE：724.285714
- net MAE：0.928571
- 结论：单纯提高整图分辨率没有收益，说明瓶颈不是像素不足，而是整图信息密度过高

### 2.5 Tile2x2：降低信息密度

将每张 panel 切成 2x2 四块，分别预测后聚合回 panel。

- node MAE：378.285714
- edge MAE：713.5
- net MAE：0.714286
- 结论：分块输入有效，尤其改善 node_count 与 net_count

### 2.6 Tile2x2 + overlap10：缓解边界截断

在 2x2 tile 基础上加入 10% overlap，减少边界线段截断。

- node MAE：362.642857
- edge MAE：687.857143
- net MAE：0.857143
- 结论：overlap10 进一步改善 node/edge，尤其验证了边界截断会影响 edge_count

## 3. 总体对比

| setting | valid rate | node MAE | edge MAE | net MAE |
| --- | ---: | ---: | ---: | ---: |
| Doubao v1 | 0.357143 | 500.857143 | 828.357143 | 3.571429 |
| Doubao prompt v2 | 1.0 | 409.285714 | 737.357143 | 16.357143 |
| Doubao prompt v3 | 1.0 | 394.642857 | 715.642857 | 0.857143 |
| Doubao prompt v3 1024 | 1.0 | 399.571429 | 724.285714 | 0.928571 |
| Doubao prompt v3 tile2x2 | 1.0 | 378.285714 | 713.5 | 0.714286 |
| Doubao prompt v3 tile2x2 overlap10 | 1.0 | 362.642857 | 687.857143 | 0.857143 |

## 4. 当前最佳方案

当前默认 image-input baseline 固化为：

- Model：Doubao
- Prompt：v3
- Input：tile2x2 + 10% overlap
- Aggregation：node/edge 求和，net 使用 `mean_clamped3`
- Evaluation：panel-level evaluator

选择依据：

- 10 / 14 个 panel 被 auto judge 判定为 `overlap_edge_benefit`
- 10 / 14 个 panel 被判定为 `better_than_whole_image`
- 仅 1 个 panel 存在 `possible_duplicate_edges`
- overlap10 获得当前最低 node MAE 与 edge MAE

## 5. 为什么暂不做全量 3x3

3x3 会将每张图从 4 个 tile 增加到 9 个 tile，API 成本与重复计数风险都会显著上升。当前 tile2x2 overlap10 已经证明 overlap 可以缓解边界截断，但仍存在 duplicate node/net 风险。因此下一步应先做 per-sample delta 分析和风险样本定位，而不是直接全量 3x3。

## 6. 下一阶段方向

下一阶段建议进入 hybrid pipeline：

- 使用传统图像处理提取线段、端点、交点候选
- 使用 OCR/符号检测定位端子排、标签、连接端子
- 使用 VLM 对 tile-level 候选进行审核或纠错
- 继续用 Topology Panel v1 evaluator 做统一评测

## 7. 关键输出

- Leaderboard：`data_index/topology_panel_v1_model_leaderboard.csv`
- Delta analysis：`data_index/topology_panel_v1_image_input_delta_analysis.csv`
- Auto judge policy：`docs/topology_panel_v1_tile2x2_overlap10_auto_judge_report.md`
- Tile overlap review：`data_index/topology_panel_v1_tile2x2_overlap10_review.html`
