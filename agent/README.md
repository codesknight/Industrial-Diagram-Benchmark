# Agent

这里放 Tool-Augmented VLM 和 CAD Agent 相关代码。

建议后续模块：

1. `tools_api.py`: 封装 parser、graph、validator、renderer 等工具调用
2. `tool_trajectory.py`: 保存模型调用工具的轨迹数据
3. `cad_agent.py`: 图纸查询、修改、生成、校验的 Agent 入口
