# 书中世界模拟器

把一本书变成**可进入、可生活、可被记住**的文字世界。

游玩时**不调用 AI**；世界在制作阶段生成、检查并保存，可离线稳定运行。

> 本仓库是可运行的第一版实现。**仅使用 Python 标准库**，无第三方依赖，无前端构建步骤。

---

## 目录

- [环境要求](#环境要求)
- [安装与启动](#安装与启动)
- [离线游玩](#离线游玩)
- [投书制作](#投书制作)
- [API Key 的本地保管方式](#api-key-的本地保管方式)
- [项目结构](#项目结构)
- [测试与验证](#测试与验证)
- [当前限制](#当前限制)
- [素材与授权说明](#素材与授权说明)
- [许可证](#许可证)

---

## 环境要求

| 项 | 要求 |
|----|------|
| Python | **3.10+**（开发验证于 3.13） |
| 依赖 | **无**。运行时与制作流程只用标准库 |
| 前端 | 原生 HTML / CSS / JS，**无需** npm 或任何构建步骤 |
| 操作系统 | 主要面向 **Windows**；游玩路径本身跨平台 |

> 仅在 Windows 上提供 `.bat` 启动脚本与 DPAPI 加密存储。其他系统可用下文的命令行方式启动。

---

## 安装与启动

### 方式一：命令行游玩（最简单，推荐先跑这个）

```bash
git clone https://github.com/<your-name>/book-world-simulator.git
cd book-world-simulator
python play.py
```

### 方式二：图形界面（Windows）

双击 **`启动杏花沟.bat`**，浏览器会自动打开 `http://127.0.0.1:8765/`。

- **停止服务**：双击 **`停止杏花沟.bat`**
- 启动脚本在后台运行服务，**关闭启动窗口不会停止服务**
- 端口默认 `8765`；若目录下存在 `.web-port` 文件，则使用其中记录的端口

### 方式三：手动起网页服务（跨平台）

```bash
python web/server.py --open
# 或指定端口
python web/server.py --port 8765 --open
```

浏览器打开 `http://127.0.0.1:8765/` 即可。服务只监听本机 `127.0.0.1`，不对外暴露。

---

## 离线游玩

**游玩路径完全不联网。** 世界是预生成的：场景、结局、人物关系与延迟后果都已落在数据包里，运行时只做确定性结算。

### 界面能力

| 模块 | 说明 |
|------|------|
| 世界 | 选择书中世界并游玩；展示封面与场景插画（插画缺失时自动降级为渐变底图） |
| 书架 | 各书封面 + 进度，一键切换并**继承原进度** |
| 投书 | 正文 → 起草并编辑结构 → 可续跑制作与质量报告（**此路径可联网**） |
| 存档 / 成就 / 设置 | 含自定义大模型 API 配置（文本 + 图像模型） |
| 创造模式 | 以「上帝的粗线」拧动关系 / 处境 / 手谕。**定数不可改写** |

### 命令行

```bash
python play.py                                   # 交互游玩样本《杏花沟》
python play.py --package data/samples/tongzilou/package
python play.py --script runs/sample_a.json       # 按脚本跑一局（自动化）
python make_playthroughs.py                      # 生成两条完整游玩台本
```

### 内容体量

**《杏花沟 · 一季秋事》**：36 个场景 · 13 种结局 · 18 个人物 · 16 个地点 · 11 个冲突源 · 8 个定数事件。

一天常只能顾一头，单周目约碰到一半场景——重开有新分支。详见 [`docs/CONTENT_MAP.md`](docs/CONTENT_MAP.md)。

---

## 投书制作

制作阶段**可联网**，也可完全离线（产出本地草稿）。

```bash
# 一键：提取结构 → 脚手架 → 可玩数据包
python production/pipeline.py all \
  data/samples/<新书>/extract/world_extract.json \
  data/samples/<新书>/package

# 只校验数据包
python play.py --validate --package data/samples/<新书>/package

# 换书回归测试
python tests/test_portability.py
```

- **L1 全自动保证**：合法 extract ⇒ 可玩世界（定数 / 风声 / 取舍 / 结局 / 延迟后果）
- **L2 可选加厚**：杏花沟那种 36 场景密度，走同一套长肉流程
- 已用第二本《筒子楼 · 分房记》与第三本《南堤渡口》验证全流程

**产品承诺：换书不换引擎。** 详见 [`docs/PORTABILITY.md`](docs/PORTABILITY.md) 与 [`docs/PRODUCTION_PIPELINE.md`](docs/PRODUCTION_PIPELINE.md)。

---

## API Key 的本地保管方式

本项目**不附带任何 API Key**，也不要求你配置。只有用到「投书加厚」「自动配图」「创造模式改写」时才需要。

### 存储方式

| 项 | 说明 |
|----|------|
| 位置 | `data/config/llm.json`（相对项目根目录） |
| 加密 | **Windows DPAPI**，绑定当前 Windows 用户；文件里只存密文 |
| 明文 | **永不落盘**；旧版明文配置在首次读取时原位迁移为密文 |
| 回显 | 网页只显示「已设置」，**不返回任何 Key 字符** |
| 清除 | 设置页可一键清除本机 Key |
| 换机 | 换电脑或换 Windows 用户后需重新填写（DPAPI 密钥不可迁移） |

### 传输约束

- 仅向 **HTTPS** 地址发送 Key；本机 `localhost` / `127.0.0.1` 允许 HTTP
- **带 Key 的请求不跟随重定向**
- 第三方错误正文与服务异常**不会回显到网页**
- 配置中的 URL 会校验 scheme、hostname、userinfo、query、fragment

### 你会发送什么给服务商

| 场景 | 发送内容 |
|------|----------|
| 勾选「文本模型加厚」 | 提取结构与脚手架场景文本 |
| 启用 API 后投书配图 | 书名、世界设定、地点描述 |
| 创造模式改写 | 当前状态与改写指令 |

> **只使用你信任的服务商，且只投喂你有权使用的文本。**

### 分享前请务必注意

- `data/config/` 与 `data/saves/` 已列入 `.gitignore`，但**截图、备份、明文旧配置**不受保护
- 历史提交（若你曾提交过）需自行用 `git filter-repo` 清理
- 若 Key 曾外泄，请到服务商后台**撤销并换新**

---

## 项目结构

```
play.py                      # 命令行入口（离线）
web/
  server.py                  # 本地网页服务（仅标准库）
  static/                    # 旧版前端，仅供回溯（现入口在根目录）
engine/                      # 与书籍解耦的运行时
  models.py                  # 世界数据包结构
  state.py                   # 持续状态：数值/旗标/关系/记忆/延迟后果
  session.py                 # 无界面会话 API（网页与测试共用）
  effects.py                 # 效果与延迟后果结算
  runner.py                  # 终端主循环
  endings.py                 # 「我成为了谁」判定
  achievements.py            # 成就
  save_store.py              # 存档槽
  shelf.py                   # 多书书架状态
  god_mode.py                # 创造模式（上帝干预与限度）
production/                  # 制作阶段（不在游玩路径上）
  PROMPTS.md                 # 结构提取 / 场景生成提示词
  extract_schema.json        # 提取契约
  scaffold.py                # extract → 可玩包（全自动保底）
  validate.py                # 数据包校验（假选择 / 空引用 / 定数无线索）
  pipeline.py                # CLI 流水线
  generate_world.py          # 可续跑分段提取与场景改写
  quality_check.py           # 内容机检与原文重合提示
  ingest.py                  # 投书入口
  image_gen.py               # 封面 / 场景图（API 或本地占位）
  llm_config.py              # 自定义 OpenAI 兼容 API
  god_llm.py                 # 创造模式后的走向改写
data/samples/xinghuagou/
  extract/world_extract.json # 结构提取结果
  package/                   # 引擎只读这个（world / scenes / endings）
  package_scaffold/          # 脚手架自动产出对照
tests/                       # 测试（三大防线 + 换书 + 安全 + 网页冒烟）
docs/                        # 流程、可移植性、验证、内容地图、遗留问题
runs/                        # 完整游玩台本
启动杏花沟.bat / 停止杏花沟.bat
assets/app-icon.png / .ico   # 应用图标
```

---

## 测试与验证

```bash
python tests/test_engine.py         # 13 项：三大防线
python tests/test_portability.py    # 10 项：换书回归
python tests/test_generation.py     #  5 项：制作流水线 + 第三本书验收
python tests/test_key_security.py   #  4 项：Key 存储与出站请求安全
python tests/test_web_smoke.py      #  3 项：网页服务冒烟

python play.py --validate           # 数据包校验
```

前端语法自检（需 Node.js，仅用于开发）：

```bash
node --check app.js
node --check web/static/app.js
```

---

## 当前限制

**请在采用前了解这些边界：**

1. **内容生产仍是半自动。** 杏花沟的 scenes / endings 基于提取结构**人工长肉**；流水线能保证「结构合法 ⇒ 可玩」，但达不到 36 场景那种密度。详见 [`docs/OPEN_ISSUES.md`](docs/OPEN_ISSUES.md)。
2. **插画素材未随仓库发布。** 见下文「素材与授权说明」。仓库内不含场景插画与书籍封面，界面会降级为渐变底图。
3. **没有许可证的第三方文本不要投喂。** 抽结构与改写会把内容发给模型服务商。
4. **DPAPI 仅 Windows。** 其他平台保存 Key 会失败；可改用手工配置文件（不推荐）。
5. **网页服务只监听本机。** 没有鉴权，**不要**暴露到公网。
6. **公开分享「由书而来」的世界前**：必须去标识化、原创化情节与角色、人工复核。**简单改名不够。**
7. **`web/static/` 是旧版 UI**，现入口在项目根目录，勿当作主入口修改。
8. **定数事件不可被玩家改写**，这是产品设计而非缺陷。

---

## 素材与授权说明

### 已发布

| 内容 | 授权状态 |
|------|----------|
| `engine/` `production/` `web/` `tests/` 全部代码 | MIT（见 LICENSE） |
| `data/samples/*/package/` 场景与结局 | 原创再创作，不含原文段落 |
| `docs/` `runs/` 文档 | 原创 |
| `assets/app-icon.png` / `.ico` | 原创应用图标，无 AIGC 元数据 |
| `tests/fixtures/nandi/source.txt` | 原创短篇（测试夹具） |

### 未发布（已从发布集中排除）

| 内容 | 原因 |
|------|------|
| `data/samples/*/source/` 原始短篇 | 创作底稿，属受控制作材料，不进公开成品 |
| 场景插画与书籍封面（8 张） | **由 AI 生成平台产出**：图中含可见水印，且 EXIF 内嵌符合 GB 45438—2025 的 AIGC 隐式标识（`ContentProducer` 指向小米 MiMo）。**用户侧再分发授权链未能确认**，故不随仓库发布 |
| `data/config/` API 配置 | 本机私密配置 |
| `data/saves/` 存档与成就 | 本机游玩进度 |

> 若你希望补上插画：请先向生成平台确认你对该输出的再分发与商用授权，再将文件放入 `assets/scenes/` 与 `assets/books/<id>/cover.png` 并同步更新 `assets/books/*/assets.json`。界面会自动加载，无需改代码。

### 贡献新素材时

请确认你有权公开该素材。**不要**提交：
- 受版权保护的书籍原文
- 第三方商标、真人肖像
- 无授权的 AI 生成图（尤其带平台水印的）
- 任何 API Key、账号信息或本机绝对路径

---

## 许可证

本项目采用 **MIT License**，详见 [LICENSE](LICENSE)。

注意：MIT 仅覆盖**本仓库内的代码与原创内容**。你自行添加的书籍文本、第三方素材、AI 生成图的授权需另行确认。
