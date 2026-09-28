# 交接文档 · 书中世界模拟器

> **给下一位接手的 AI / 工程师**  
> 项目根目录：本文件所在目录（即仓库根）  
> 最后更新：随本文  
> 测试状态：`tests/test_engine.py` 13 项 OK · `tests/test_portability.py` 10 项 OK ·
> `tests/test_web_smoke.py` 3 项 OK · `tests/test_generation.py` 5 项 OK ·
> `tests/test_key_security.py` 4 项 OK（共 35 项）

---

## 0. 一句话产品

**把一本书变成可进入的文字世界。**  
玩家以书中普通人身份，在信息不全、资源有限、时间不等人的情况下生活与选择。  
原书大事件照常发生（历史不转弯）；玩家改变处境、关系、代价、名声和结局（「我成为了什么样的人」）。

产品意图见：仓库内 `docs/` 下的流程与验收文档（及实现中体现的验收标准）。

---

## 1. 必须守住的产品原则

违反这些等于产品失败，请当硬约束：

1. **游玩时默认不强制联网**。世界预生成、可离线玩；AI 在**制作/配图/创造模式改写**时按需调用。
2. **选择改变持续状态**。人物记得玩家做过的事；至少有跨场景延迟后果。
3. **定数不转弯**。书中写定的大事按时发生；可被风声/物价/人际预感，不可被轻易改写。
4. **小世界必须有可玩冲突**。面子、人情债、土地/房产、婚丧、离开与归来。
5. **人物有欲望、阻碍、代价和说话方式**。禁止设定集腔、空泛对话、明显善恶选项。
6. **书与引擎分离**。换书主要换 `data/`，不改 `engine/`。
7. **版权**：原文仅受控使用，不进公开成品；提取结构而非复述段落。

---

## 2. 怎么跑起来

### 图形界面（主路径）

```bat
启动杏花沟.bat
```

或：

```bat
python web\server.py --open
```

浏览器打开 `http://127.0.0.1:8765/`（入口为项目根目录 `index.html`）。  
停止：`停止杏花沟.bat`。

### 命令行游玩 / 测试

```bat
python play.py
python play.py --validate
python tests\test_engine.py
python tests\test_portability.py
python tests\test_generation.py
python make_playthroughs.py
python production\pipeline.py all data\samples\tongzilou\extract\world_extract.json data\samples\tongzilou\package
```

### 运行时依赖

- Python 3.12+（本机：`MIMO_PYTHON` 指向的便携 Python）
- **标准库 only**（`http.server` / `urllib` / `json` / `pathlib`）。无 Flask、无前端构建步骤。
- 前端：原生 HTML/CSS/JS，根目录 `index.html` + `style.css` + `app.js`。

---

## 3. 目录地图

```
index.html / style.css / app.js   # 应用入口（手机可适配）
play.py                           # 终端游玩
web/server.py                     # 本地 HTTP API + 静态托管
engine/                           # 与书籍解耦的运行时
  models.py                       # 世界数据包 schema
  state.py                        # 持续状态（数值/旗标/关系/记忆/延迟）
  session.py                      # 无界面会话 API（网页/测试共用）
  effects.py                      # 效果与延迟后果
  endings.py                      # 「我成为了谁」
  achievements.py                 # 成就
  save_store.py                   # 存档槽
  shelf.py                        # 多书书架状态
  god_mode.py                     # 创造模式（上帝干预与限度）
  runner.py                       # 终端主循环
production/                       # 制作阶段（可联网）
  extract_schema.json             # 提取契约
  PROMPTS.md                      # 提取/长肉提示词
  scaffold.py                     # extract → 可玩包（全自动保底）
  validate.py                     # 数据包校验（假选择/空引用/定数无线索）
  pipeline.py                     # CLI：validate-extract / scaffold / check / generate
  generate_world.py               # 可续跑分段提取与场景/结局改写（--llm 显式调用模型）
  quality_check.py                # 内容机检与原文重合提示
  ingest.py                       # 投书入口（起草 extract + 打包）
  image_gen.py                    # 封面/场景图（API 或本地占位）
  llm_config.py                   # 自定义 OpenAI 兼容 API
  god_llm.py                      # 创造模式后的走向改写
  expand_*.py / rebalance.py      # 杏花沟内容扩充脚本（历史产物）
data/
  samples/xinghuagou/             # 加厚样例（36 场景）
    source/  extract/  package/  package_scaffold/
  samples/tongzilou/              # 换书验证（脚手架，约 20 场景）
    extract/  package/
  saves/                          # 存档 slot_*.json + _meta.json（成就）
  config/llm.json                 # API 配置（Key 由 Windows DPAPI 加密，仍勿公开）
assets/
  scenes/                         # 通用场景插画
  books/<id>/cover.png + assets.json
tests/
docs/                             # PORTABILITY / VERIFICATION / FLOW / OPEN_ISSUES / CONTENT_MAP
runs/                             # 自动双线试玩台本
```

**过时目录**：`web/static/` 是旧版 UI，现入口在根目录；勿当主入口改。

---

## 4. 核心数据契约

### 4.1 Extract（制作输入）

见 `production/extract_schema.json`。必填：

- `meta.source_id / source_title`
- `world_frame`：scale, setting, time_unit, power_map, threat_style
- `conflict_sources` ≥4（type/description/stakes）
- `characters` ≥5（**wants / blocks / costs / speech_style**）
- `canon_events` ≥4（turn 递增，**foreshadow ≥2**，线索 turn **早于**事件）
- `player_suggestions`、`play_space_note`

校验：`python production/pipeline.py validate-extract <extract.json>`

### 4.2 世界数据包（引擎只读这个）

`package/world.json` + `scenes.json` + `endings.json`

- **stats**：money, face, guts, warmth, craft, health, favor_out, favor_in（书可扩展）
- **scenes**：trigger（turn/window/flag/unlocked…）、narration、choices→effects+hooks
- **hooks.delay**：2–12 回合后经具体的人回来
- **endings**：conditions + **epithet**（「我成为了谁」）

校验：`python play.py --validate` 或 `production.validate.validate_package`

### 4.3 存档

`data/saves/slot_*.json`：`{ package_id, package_title, player_id, state, phase, ending, ... }`  
`GameState.to_dict/from_dict` 可完整序列化。  
书架槽位命名：`book_<package_meta_id>`。

---

## 5. 系统架构（简图）

```
[原文] --制作(可AI)--> extract --scaffold/长肉--> package
                                              |
                     [web API] <--- engine.session.GameSession
                          |           （游玩离线也可 GameSession）
                    index.html
                    存档 / 书架 / 成就 / 创造模式 / 配图 / LLM配置
```

- **换书不换引擎**：`GameSession` / `validate` / 前端均吃 package。
- **自动化地板**：任意合法 extract → scaffold → 可玩（有定数/风声/取舍/结局）。
- **品质天花板**：人工/LLM 长肉（杏花沟 36 场景）。

---

## 6. HTTP API（`web/server.py`，默认 8765）

| 方法 | 路径 | 作用 |
|------|------|------|
| GET | `/api/info` | 书目列表（含 cover / place_art） |
| GET | `/api/books` | 同上精简 |
| POST | `/api/new_game` | 新开一局 `{book}` |
| POST | `/api/choose` | `{sid, choice_id, scene_id?}` |
| GET/POST | `/api/saves` `/api/save_write` `/api/save_load` `/api/save_delete` | 存档 |
| POST | `/api/shelf_save` `/api/shelf_load` | 书架切换与进度继承 |
| GET | `/api/shelf` | 各书进度 |
| GET | `/api/achievements` | 成就 |
| POST | `/api/game_meta` `/api/meta_reset` | 跨周目元数据 |
| GET/POST | `/api/llm_config` `/api/llm_config_save` `/api/llm_test` | 自定义 API |
| POST | `/api/ingest` | `mode=draft\|extract` 投书 |
| GET | `/api/god_limits` | 创造模式限度 |
| POST | `/api/god_apply` | 上帝干预 + 可选 LLM 改写走向 |

前端主文件：`app.js`（`api()` 封装上述）。

---

## 7. 前端功能清单

- 世界选择（封面）→ 游玩（场景插画、状态、风声、延迟、记忆）
- **侧栏书架**：封面+进度，一键切换，**继承原进度**
- **投书**：正文 → 起草并编辑 extract → 可续跑制作与质量报告 → **自动封面/场景图**；文本模型需显式勾选，本地草稿可试玩但仍须人工复核
- **存档**：多槽 / 自动 / 快速 / 重开（可确认）
- **成就**：18 项，跨周目
- **创造模式**：关系/数值/态度/手谕；改定数会被拦
- **设置**：主题（宣纸/墨夜）、字号、玻璃柔光、动效、序号、自动存档、确认、Toast、LLM（文本+图像模型）
- 移动端响应式（侧栏抽屉、缩小取景）

---

## 8. 创造模式与「上帝限度」

`engine/god_mode.py`：

- **可改**：关系 ±25、数值 ±15、态度旗标、手谕（写入 `god_directive` 等）
- **不可改**：定数发生与否、定数时间、原书写死结果
- 改定数 → `ok: False` + 成就「上帝也救不了」

`production/god_llm.py`：干预后生成「命运侧写 + 后续 beats + 警告」。  
有 API 则用模型，否则本地模板。结果写入记忆/旗标。

---

## 9. 联网策略（请保持灵活而非一刀切）

| 场景 | 联网 |
|------|------|
| 投书起草 extract（可选精修） | 可 |
| 投书自动配图 | 可 |
| 创造模式改写走向 | 可 |
| 日常游玩/读档/切书 | 不需要 |
| 无 Key / 失败 | 本地降级，流程不断 |

配置：`data/config/llm.json`（`enabled, base_url, api_key_protected, model, image_model, ...`）。旧明文 Key 首次读取时原位迁移为当前 Windows 用户可解的密文；网页只返回是否已设置。  
OpenAI 兼容：`/v1/chat/completions`、`/v1/images/generations`。

---

## 10. 样本世界

| | 杏花沟 xinghuagou | 筒子楼 tongzi_low |
|--|------------------|-------------------|
| 路径 | `data/samples/xinghuagou/package` | `data/samples/tongzilou/package` |
| 定位 | 加厚样例 36 场景 13 结局 18 人 | 换书验证（脚手架） |
| 原文 | 原创短篇（制作用） | 原创 extract（无长篇原文） |
| 书 id | `xinghuagou` | `tongzi_low`（注意 ≠ 目录名 `tongzilou`） |

**书 id 以 package `meta.id` 为准**，不是文件夹名。

---

## 11. 测试与验证

```bat
python tests\test_engine.py        # 假选择、定数必现、延迟后果、结局分叉
python tests\test_portability.py   # 双书 extract/scaffold/同引擎跑通
python tests\test_generation.py    # 第三本原创短篇、内容报告、模型模拟与断点续跑
python play.py --validate
```

双线台本：`runs/playthrough_*.md`，摘要 `docs/PLAYTHROUGH.md`。  
防线说明：`docs/VERIFICATION.md`。  
换书保证：`docs/PORTABILITY.md`。

---

## 12. 已知问题 / 待办（优先级）

### P0 内容与自动化
1. 真实文本 API 输出质量仍待有 Key 时逐幕验收；批跑命令与边界见 `docs/PRODUCTION_PIPELINE.md`
2. 筒子楼未加厚到杏花沟密度
3. 对白「正确的废话」自动鉴别

### P1 体验
4. 面子/硬气极端路线贴 0/100
5. 多人同场关系分摊偏粗
6. 创造模式「一键撤销」、手谕强制影响下一幕必选
7. 存档缩略/导出

### P2 工程
8. 版权书受控投喂沙箱、去标识化检查工具
9. 专精流台本扫全分支（单周目约碰一半场景）
10. 清理 `web/static/` 旧 UI、清理 `production/expand_*.py` 为「示例脚本」并文档化

### 设计张力（勿「修掉」）
- 历史不转弯 vs 选择有后果  
- 离线稳定 vs 创造模式/制作要 AI  
- 自动脚手架保底 vs 加厚后的文学密度  

---

## 13. 给 GPT 的续做建议

1. **先跑测试**，确认环境 Python 可用且 23 项全绿。
2. **改引擎前先读** `engine/models.py` + `engine/session.py`；改数据只动 `data/samples/**`。
3. **加书**：本地可用 `production/pipeline.py generate --extract ... --out ...` 产出可玩草稿；显式加 `--llm` 才做模型加厚，详见 `docs/PRODUCTION_PIPELINE.md`。
4. **不要**在游玩热路径引入网络调用；保持 `GameSession` 纯本地。
5. **不要**把手工剧情说成「投书自动生成」；自动化地板是 scaffold。
6. UI 改动改根目录 `index.html/style.css/app.js`，并保持手机布局。
7. 密钥只通过设置页录入；配置文件中仅保留 DPAPI 密文，勿写死在代码/文档或提交配置文件。

---

## 14. 快速验收清单（移交前）

- [ ] `启动杏花沟.bat` 能打开 UI
- [ ] 能进杏花沟并做出至少一个选择
- [ ] 侧栏切换到筒子楼再切回，进度仍在
- [ ] 存档 / 读档 / 成就页正常
- [ ] 创造模式改关系成功；改定数被拒
- [ ] 投书入口能 draft + 生成包（无 Key 也有占位封面）
- [ ] `tests\test_engine.py`、`tests\test_portability.py`、`tests\test_web_smoke.py` 与 `tests\test_generation.py` 全过

---

## 15. 联系上下文（意图金句）

> **我想在一场走向已知的岁月里，以一个普通人的身份，活出一段属于我自己的、会被人记住的经历。**

一切功能取舍回到这句话。

---

*本文为交接主文档。更细的设计说明在 `docs/`；产品验收以《意图描述》+ 本文原则为准。*
