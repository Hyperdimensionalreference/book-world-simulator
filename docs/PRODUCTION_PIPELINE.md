# 投书制作流水线

`production/generate_world.py` 把结构提取、脚手架、场景与结局改写、结构校验、内容复核串成一次可续跑制作。它只在**制作阶段**运行；`engine/` 的游玩过程仍完全离线。

网页「投书」的结构编辑完成后也调用这条流水线。默认产出本地脚手架草稿；只有勾选「使用已配置的文本模型加厚」才把当前 extract 和脚手架场景发送到文本 API。网页上传的正文用于本地原文重合检查，暂存文件会在制作后删除，不保存为 `source/book.txt`；如需保留书稿，请自行在受控位置备份。配图按图像 API 设置另行执行。

网页制作记录位于 `data/samples/<书 id>/.package_production/`，包括 `extract.json`、检查点和 `quality_report.json`。模型中断后保持相同 extract、正文和模型设置再次生成，可复用成功步骤。同名数据包已经存在时网页会拒绝覆盖；需要新版本请先给 extract 的 `meta.source_id` 使用新 id。网页会把可玩的草稿加入**本机**世界列表，并显示阻断项和提醒；加入列表不代表通过发布验收。

## 两种输入

有已审阅的 extract 时，从结构直接制作：

```powershell
python production/pipeline.py generate --extract tests/fixtures/nandi/extract.json --source tests/fixtures/nandi/source.txt --source-type original_sample --out data/samples/nandi_ferry/package
```

`--source` 在这种用法中只供本地原文重合检查；模型改写时也只会看到 extract 和脚手架场景。若不需要重合检查，可省略它。

只有书稿时，先生成可编辑结构草稿，再产出可玩包：

```powershell
python production/pipeline.py generate --source path/to/book.txt --title "书名" --id book_example --out data/samples/book_example/package
```

默认是**本地草稿**：它使用启发式提取和脚手架，能够游玩，但会在质量报告中标出占位文案。请修改工作目录中的 `extract.json`，再以 `--extract` 制作正式候选包。不要把本地草稿称为已经理解原著的成品。

## 模型加厚

在设置里配置并启用文本 API 后，显式加 `--llm`：

```powershell
python production/pipeline.py generate --source path/to/book.txt --title "书名" --id book_example --out data/samples/book_example/package --llm
```

这会把书稿按约 5500 字符分段发送到配置的文本服务，汇总结构笔记，再逐场改写叙述、对白、选项和延迟回响，最后改写结局。脚手架的回合、定数、条件和效果保持固定。**只有显式使用 `--llm` 才发送书稿。**若输入已审阅的 extract，模型阶段从 extract 开始。

生产过程在输出包的同级 `.<包目录名>_production/` 保存 `manifest.json`、`extract.json`、各步骤检查点和 `quality_report.json`。它不复制书稿文件，但模型返回的笔记可能包含引文；整个工作目录都应按受控材料保存。API Key 只从 `data/config/llm.json` 读取，不写入检查点。

中断后用相同输入、模式与模型继续：

```powershell
python production/pipeline.py generate --source path/to/book.txt --title "书名" --id book_example --out data/samples/book_example/package --llm --resume --force
```

`--resume` 复用输入摘要和模型一致的成功步骤；`--force` 只覆盖输出包的三个 JSON 文件。换书稿、模式或模型时请使用新的工作目录。已有包未加 `--force` 时不会覆盖。

## 验收与人工复核

每次制作先运行结构校验，再输出质量报告。报告会标出占位文案、重复选项与重复代价组合、对白缺席、重要站位缺少延迟回响、后果无人承接或时距异常，以及与输入原文连续 28 字以上的重合。`--strict` 在存在阻断项时返回退出码 2；它仍会保留可试玩包和报告，便于修订。

机器检查只能发现部分问题。发布前仍需逐幕检查人物口吻、取舍重量、定数预感与版权边界；简单改名不构成去标识化。真实文本 API 的输出质量需在配置 Key 后另做验收。

第三本原创短篇测试材料位于 `tests/fixtures/nandi/`，默认不会出现在玩家书架。回归命令：

```powershell
python tests/test_generation.py
python tests/test_engine.py
python tests/test_portability.py
python tests/test_web_smoke.py
```
