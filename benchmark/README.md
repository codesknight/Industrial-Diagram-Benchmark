# Benchmark

这里放评估脚本和评估协议实现。

优先级建议：

1. `manifest_eval.py`: 检查样本覆盖率和划分稳定性
2. `json_eval.py`: JSON 合法性、字段完整度、编辑距离
3. `graph_eval.py`: 节点、边、连通关系 F1
4. `vqa_eval.py`: 图纸问答准确率
5. `cad_eval.py`: CAD 重建一致性与渲染相似度
