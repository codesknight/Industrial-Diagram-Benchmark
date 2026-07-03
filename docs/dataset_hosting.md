# Dataset Hosting

本项目采用双仓库管理：

- GitHub: 管理代码、配置、文档、索引和评估脚本
- Hugging Face Dataset: 管理大体积 DWG/DXF/JSON/PNG 数据

## Links

- GitHub: `https://github.com/codesknight/Industrial-Diagram-Benchmark`
- Hugging Face Dataset: `https://huggingface.co/datasets/yanhongliu/Industrial-Diagram-Benchmark`

## Local Data Restore

安装依赖：

```powershell
pip install -r requirements.txt
```

下载完整数据：

```powershell
python scripts/download_dataset.py
```

下载后默认写入：

```text
datas/
```

该目录已被 `.gitignore` 忽略，不会被普通 Git 提交。

## Recommended Workflow

1. 在 Hugging Face Dataset 更新原始数据或中间产物。
2. 在本地运行 `python scripts/download_dataset.py` 同步数据。
3. 运行 `python scripts/build_dataset_manifest.py` 重新生成索引。
4. 将代码、配置、文档、`data_index/` 提交到 GitHub。

## Notes

当前 GitHub 仓库不直接追踪 `datas/`，避免把数 GB 的二进制文件塞进普通 Git 历史。
