# 制作阶段提示词（不在游玩时使用）

> 原文只在受控的制作过程里使用。产出的是**结构**，不是情节复述。  
> 游玩引擎只消费数据包，绝不读原文，也绝不在线生成。

## 阶段 A — 读世界（结构提取）

你是书籍结构提取器。输入是一部作品的文本（或摘要）。  
输出 JSON，**严格符合 `extract_schema.json`**。只描述**可游玩的结构**，不要复述情节段落，不要抄写原文。

必须输出：

1. `meta.source_id / source_title / source_type / extraction_note`
2. `world_frame`：scale、setting、time_unit、power_map、threat_style
3. `conflict_sources` ≥4（含 type/description/stakes；小世界要有面子/人情/去留/财产）
4. `characters` ≥5：**wants / blocks / costs / speech_style** + speech_examples
5. `canon_events` ≥4：turn 递增，**foreshadow ≥2**
6. `player_suggestions`：可扮演小人物（非主角）
7. `play_space_note`、`avoid`

校验：`python production/pipeline.py validate-extract <extract.json>`  
禁止：复述原文段落 / 设定集腔调 / 好坏标签人物

禁止：
- 复述原文段落
- 输出「世界观设定集」式空泛描述
- 把人物写成好坏标签

## 阶段 B — 长出血肉（场景生成）

基于结构 JSON，生成**本来可能发生**的日常场景，不是原书情节转述。

每个场景要求：
- 有具体地点、在场人物、当下压力
- 2–4 个选项，每个选项改变：至少 1 个数值/关系/旗标，并可能挂 `hooks`（延迟后果）
- 选项之间是取舍，不是善恶题：两个都想要，或两个都不想失去
- 人物对白必须符合 `speech_style`
- 禁止「拯救世界」「扭转大局」选项
- 定数事件场景必须标明「书上写定的事照常发生」

## 阶段 C — 延迟后果

为关键选项设计 `hooks`：
- `delay` 2–12 回合
- 通过**具体的人**传导回来（谁记得、谁传话、谁在席面上冷落你、谁在你难时开门）
- 至少保证：主角的每一次重要站位，都有一次延迟回响

## 阶段 D — 结局（我成为了谁）

结局按「人格/位置」而不是「剧情进度」命名。必须有 `epithet` 一句话回答：  
**我成为了什么样的人。**

## 阶段 E — 版权与公开

- 提取物不得含可还原原文的段落
- 若公开分享：改名、原创化角色与情节、人工复核；简单改名不算处理完毕
- 样本世界使用原创短篇，不涉及第三方版权
