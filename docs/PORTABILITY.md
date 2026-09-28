# 换书一定行吗？——可移植性说明

产品要求：**投入一本书 → 可玩世界**，不能只对《杏花沟》手调得好。  
本文说明保证到哪一层、怎么复现、以及诚实的边界。

---

## 一、保证模型（两层）

```
                    ┌─────────────────────────┐
  任意书籍原文 ──►  │ 阶段A 结构提取 extract   │  必须符合 extract_schema.json
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ scaffold.py 脚手架      │  全自动、可重复
                    │ 保底可玩包              │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ （可选）长肉：场景/对白  │  PROMPTS 阶段B/C/D
                    │ 人工或 LLM，质量加厚    │  → 杏花沟那种密度
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ validate + 试玩门槛     │  tests/test_portability.py
                    └─────────────────────────┘
```

| 层级 | 是否保证 | 说明 |
|------|----------|------|
| **L1 结构保底** | ✅ 全自动保证 | extract 合法 ⇒ 必能打包成可玩世界：定数、风声、取舍、结局、延迟后果 |
| **L2 体验密度** | ✅ 可选加厚 | 杏花沟 36 场景是加厚样例；第二本可走同一套加厚流程 |
| **游玩稳定性** | ✅ 保证 | 与书无关的 `engine/`，游玩时零模型、可离线 |
| **文学品质天花板** | ⚠️ 不自动 | 对白文学性、多跳人情网、数值手感需要加厚阶段 |

**换句话说**：换一本小说，**一定**能得到能玩、能结档、「我成为了谁」的世界；  
要到杏花沟那种「想多待一会儿」的密度，用同一套加厚流程，而不是改引擎。

---

## 二、已验证的两本书

| | 《杏花沟 · 一季秋事》 | 《筒子楼 · 分房记》 |
|--|----------------------|-------------------|
| 时代空间 | 北方山村，秋到年关 | 1987 厂区筒子楼 |
| scale | village | one_street |
| 主冲突 | 土地/彩礼/丧事/去留 | 分房/比武/婚事/工伤/裁员 |
| 来源 | 原创短篇手工加厚 | **同一 extract schema → scaffold 全自动** |
| 引擎 | 同一 `engine/` | 同一 `engine/` |
| 测试 | `test_engine.py` | `test_portability.py` |

已跑通：

```bash
# 第二本：从提取到可玩
python production/pipeline.py all \
  data/samples/tongzilou/extract/world_extract.json \
  data/samples/tongzilou/package

# 换书门槛测试（10 项）
python tests/test_portability.py

# 杏花沟结构也能脚手架出保底包（证明非手工特例）
python production/pipeline.py all \
  data/samples/xinghuagou/extract/world_extract.json \
  data/samples/xinghuagou/package_scaffold
```

---

## 三、第三本书怎么接

1. **原文**放在受控环境（不进公开包）。
2. 按 `production/extract_schema.json` 填 extract（或按 `PROMPTS.md` 阶段 A 让模型抽）。  
   必填：`world_frame`、≥4 冲突源、≥5 人物（wants/blocks/costs/speech_style）、≥4 定数（各≥2 条提前线索）、`play_space_note`。
3. `python production/pipeline.py all <extract> <package_dir>`
4. 立刻可玩。若要加厚：`PROMPTS.md` 阶段 B/C/D 补场景与延迟后果，再 `pipeline.py check`。
5. `python tests/test_portability.py` 可把新书加进 `BOOKS` 表一起回归。

**引擎、前端、快捷方式都���用改。**

---

## 四、质量门槛（自动拦什么）

`production/validate.py` + `scaffold.validate_extract`：

- extract 缺关键字段 / 定数线索不早于事件 / 小世界张力类型不足
- 数据包空引用、假选择（效果全同）、结局无「你是谁」
- 脚手架包必须能 `GameSession` 跑到 `finished` 且定数旗标齐全

---

## 五、诚实边界（避免「伪自动化」）

| 已做到 | 没做到（需下一步） |
|--------|-------------------|
| extract 契约 + 自动脚手架 + 三书结构验证；B/C 批跑脚本及检查点 | 真实文本 API 输出的人工质量验收 |
| 引擎/数据/前端与书无关 | 原文受控投喂的沙箱自动化 |
| 结构层冲突/风声/结局保证；明显占位、重复和薄弱后果机检 | 对白与「正确的废话」的完整自动鉴别 |
| 杏花沟加厚样例 | 每本书都自动达到杏花沟密度 |

**我们不把「手写一本好故事」说成「投书自动生成」。**  
自动化保证的是**结构与可玩**；文学密度是同一套流程上的加厚步骤，第二本已用纯脚手架跑通全流程。

---

## 六、一句话

**换一本书，世界会换，引擎不换，体验骨架不塌。**  
这是产品承诺，也是 `tests/test_portability.py` 在守的东西。
