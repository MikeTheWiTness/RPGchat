# PRD: RPG Chat Agent v1

## Problem Statement

TRPG（桌上角色扮演游戏）的数字化体验存在明显断层：

- **传统 TRPG** 需要主持人（GM）、固定地点、凑齐玩家，门槛高，难以随时随地进行
- **电子 RPG 游戏** 是预设好的线性剧情，玩家选择有限，缺乏真人 GM 的灵活性和即兴创作能力
- **AI 聊天机器人** 可以和玩家对话，但缺乏连贯的世界观、角色一致性、规则系统和叙事结构
- **AI 小说生成工具** 能生成故事，但玩家只能被动阅读，缺乏参与感和互动性

玩家需要的是一个**既能像真人 GM 一样灵活即兴，又能随时随地进行**的 TRPG 体验——有一致的角色、连贯的世界观、清晰的规则感，同时支持主动参与（玩家扮演角色）和被动观赏（AI 自动推演）两种模式。

## Solution

RPG Chat Agent 是一个基于 LLM 的 TRPG 叙事引擎，核心特征：

1. **双核心模式**：玩家参与模式（扮演角色互动）+ 玩家空缺模式（自动推演故事），两者都是核心体验
2. **角色一致性**：每个角色有独立的档案和上下文，LLM 生成时严格遵守角色设定
3. **柔性叙事**：发言顺序是建议而非强制，玩家永远可以打断和干预
4. **分层机制**：玩家侧用严谨的 d20 骰子检定，NPC 侧用运势系统做软调节
5. **检查点驱动**：通过检查点控制上下文长度，同时更新角色档案和环境状态
6. **预设生态**：支持角色预设、世界观预设、完整模组，可复用可分享

---

## User Stories

### 游戏创建与初始流程

1. 作为玩家，我想输入一段战役背景描述，系统自动生成初始世界观和角色，这样我可以快速开始游戏
2. 作为玩家，我想从预设模组中选择一个直接开始，这样不用自己设定背景
3. 作为玩家，我想选择运行模式（玩家参与/玩家空缺），这样我可以根据心情决定是参与还是观赏
4. 作为玩家，我想选择是否启用规则集成（纯叙事/轻量规则），这样我可以控制游戏的机制深度
5. 作为玩家，我想导入角色预设有哪些可选，这样我可以快速建立 PC
6. 作为玩家，我想在游戏开始前编辑 PC 的角色档案，这样我可以精确设定我的角色
7. 作为玩家，我想看到游戏开始时的初始环境描述，这样我可以知道我身处何地

### 玩家参与模式 - 基础交互

8. 作为玩家，我想输入 PC 的动作单元（对话+行动+内心活动），这样我可以扮演角色
9. 作为玩家，我想用 `【】` 标记对话、`（）` 标记内心活动，这样输入方式自然直观
10. 作为玩家，我想输入 `{继续}` 让系统推进下一步，这样我可以看到 NPC 的反应
11. 作为玩家，我想输入 `{到我}` 让系统连续推进直到轮到 PC，这样我可以快进到我的回合
12. 作为玩家，我想随时打断 NPC 的发言直接输入 PC 动作，这样我可以控制节奏
13. 作为玩家，我想看到所有角色的内心活动（全知视角），这样我可以更好地理解剧情
14. 作为玩家，我想看到判断机制的推荐理由，这样我能理解为什么是这个角色发言

### 玩家空缺模式 - 自动推演

15. 作为观众/导演，我想让故事自动推演，这样我可以像看小说一样体验剧情
16. 作为观众/导演，我想在检查点时自动暂停，这样我有时间消化剧情并可以干预
17. 作为观众/导演，我想通过 Agent 指令随时干预剧情，这样我可以控制故事走向
18. 作为观众/导演，我想看到所有角色的内心活动，这样我能全面理解角色动机
19. 作为观众/导演，我想在检查点确认后继续推演，这样我有掌控感

### 角色系统

20. 作为玩家，我想查看任意角色的档案，这样我能了解角色的详细设定
21. 作为玩家，我想看到新 NPC 入场时自动生成角色档案，这样叙事更连贯
22. 作为玩家，我想通过 `{修改角色}` 指令直接修改角色档案，这样我可以纠正或调整
23. 作为玩家，我想让角色档案在检查点时自动更新（性格成长、关系变化等），这样角色有发展感
24. 作为玩家，我想在检查点时选择是否清理离场角色的上下文，这样我可以控制信息保留
25. 作为玩家，我想角色档案在离场后仍然保留（不删除），这样角色再次出场时保持一致

### 环境系统

26. 作为玩家，我想看到环境变化的描述（天气、时间、场景物品等），这样更有沉浸感
27. 作为玩家，我想环境动作单元自然地插入到角色互动之间，这样叙事不脱离环境
28. 作为玩家，我想环境条目有可见性控制（有些信息只有特定角色知道），这样可以有悬念
29. 作为玩家，我想在场人员列表自动维护（入场/离场自动更新），这样不用手动管理
30. 作为玩家，我想系统定期校验在场人员列表的一致性，这样不会因为 LLM 遗漏而出错

### 骰子检定系统（玩家侧）

31. 作为玩家，我想通过 `{检定 技能名 DC}` 触发骰子检定，这样我可以进行技能挑战
32. 作为玩家，我想看到检定结果（投出点数 + 技能加值 vs DC），这样结果清晰透明
33. 作为玩家，我想看到自然 20 的暴击和自然 1 的大失败，这样有戏剧性
34. 作为玩家，我想检定结果嵌入到动作单元的叙事中，而不是独立的数字，这样更有沉浸感
35. 作为玩家，我想可以指定 DC，也可以让系统根据情境自动判断难度，这样灵活方便

### 运势系统（NPC 侧）

36. 作为玩家，我想看到每个 NPC 当前的运势等级，这样我能理解 NPC 的行为倾向
37. 作为玩家，我想运势在每个检查点刷新，这样有阶段性的变化感
38. 作为玩家，我想运势影响 NPC 的行为但不直接决定成败，这样既有意外感又不失控
39. 作为玩家，我想大吉/大凶的概率比较低（各 5%），这样出现时特别有戏剧性
40. 作为玩家，我想运势是角色独立的，不同角色有不同状态，这样更真实

### 检查点与上下文压缩

41. 作为玩家，我想 Agent 可以提议检查点，这样我知道什么时候该暂停消化
42. 作为玩家，我想可以手动触发检查点（`{检查点}`），这样我可以控制节奏
43. 作为玩家，我想检查点需要我确认才能生效，这样重大变化我有决定权
44. 作为玩家，我想场景切换时自动触发检查点，这样场景之间有清晰的边界
45. 作为玩家，我想检查点时生成上下文摘要，这样上下文不会无限膨胀
46. 作为玩家，我想检查点时更新角色档案，这样角色随剧情发展而成长
47. 作为玩家，我想检查点时清理过期的环境条目，这样环境信息保持新鲜
48. 作为玩家，我想在检查点时选择清理哪些离场角色的上下文，这样我可以保留重要角色的信息

### 预设系统

49. 作为玩家，我想列出可用的角色预设，这样我知道有哪些角色可选
50. 作为玩家，我想导入角色预设有哪些，这样我可以快速加入角色
51. 作为玩家，我想列出可用的世界观预设，这样我可以快速建立世界
52. 作为玩家，我想导入世界观预设，这样我可以快速开始游戏
53. 作为玩家，我想预设是跨战役可复用的，这样我在不同游戏中都能使用喜欢的角色
54. 作为玩家，我想有「模组」的概念（完整的冒险包），这样可以一键开始完整的冒险

### 持久化

55. 作为玩家，我想保存游戏进度，这样我可以随时退出下次继续
56. 作为玩家，我想加载之前的存档，这样游戏进度不会丢失
57. 作为玩家，我想保存所有状态（角色档案、上下文、环境、检查点等），这样加载后完全一致
58. 作为玩家，我想存档是本地文件，这样我的数据在自己手里

### Agent 指令

59. 作为玩家，我想用 `{}` 包裹的语法输入 Agent 指令，这样和普通动作单元区分开
60. 作为玩家，我想有 `{帮助}` 指令查看所有可用指令，这样我不用记
61. 作为玩家，我想 `{保存}` 和 `{加载}` 指令管理存档
62. 作为玩家，我想 `{角色列表}` 查看所有角色
63. 作为玩家，我想 `{角色档案 角色名}` 查看详细设定
64. 作为玩家，我想 `{修改角色 角色ID 字段 值}` 直接修改档案
65. 作为玩家，我想 `{检查点}` 手动触发检查点
66. 作为玩家，我想 `{切换场景 场景名}` 切换场景
67. 作为玩家，我想 `{检定 技能 DC}` 触发骰子检定
68. 作为玩家，我想 `{导入角色 名称}` 和 `{导入世界观 名称}` 导入预设
69. 作为玩家，我想 `{列出角色预设}` 和 `{列出世界观预设}` 浏览预设库

### 玩家确认原则

70. 作为玩家，我想场景切换需要我确认，这样重大变化不突兀
71. 作为玩家，我想检查点触发需要我确认，这样我掌握节奏
72. 作为玩家，我想时间快进需要我确认，这样叙事节奏我能控制
73. 作为玩家，我想角色档案重大变更需要我确认，这样角色发展不跑偏
74. 作为玩家，我想可以通过 Agent 指令绕过确认（强制执行），这样高级玩家有完全控制权

### 叙事体验

75. 作为玩家，我想 NPC 的发言符合其角色设定，这样角色一致不崩人设
76. 作为玩家，我想 NPC 看不到其他角色的内心活动，这样行为逻辑合理
77. 作为玩家，我想 NPC 只能感知到对自己可见的环境信息，这样信息差有意义
78. 作为玩家，我想环境动作单元定期插入（不连续太多角色对话），这样叙事不脱离环境
79. 作为玩家，我想判断机制根据情境推荐发言人，而不是机械轮流，这样更自然
80. 作为玩家，我想发言顺序是柔性建议，这样我随时可以打断

---

## Implementation Decisions

### 架构概览

采用分层架构，从内到外依次为：领域模型 → 纯逻辑子系统 → LLM 驱动子系统 → 游戏循环协调层 → 用户界面层。

核心原则：
- **LLM 是黑盒**：所有 LLM 交互都通过结构化 JSON 输入输出，系统逻辑与 LLM 生成质量解耦
- **单一真相来源**：角色动作单元历史是唯一真相，公开对话历史等均为推导数据
- **玩家最高权限**：玩家永远可以通过 Agent 指令覆盖任何自动决策

### 模块 1: 核心领域模型

**职责**：定义所有核心数据结构和类型，是整个系统的基础。

**核心类型**：

```
ActionUnit:
  character_id: str | None    # None 表示环境
  dialogue: str | None
  action: str | None
  inner_thought: str | None
  audience: list[str] | None
  entered: list[str] | None
  left: list[str] | None
  timestamp: int

CharacterProfile:
  id: str
  name: str
  character_type: "pc" | "npc"
  personality: str
  background: str
  appearance: str
  clothing: str
  skills: dict[str, int]        # 技能加值
  attributes: dict[str, int]    # 属性值
  relationships: dict[str, str]
  notes: str
  physique: dict                # height, weight, build, measurements
  identity: dict                # occupation, social_status, affiliations
  behavior: dict                # habits, quirks, mannerisms
  intimate_features: str

CharacterContext:
  character_id: str
  action_units: list[ActionUnit]
  summary: str | None           # 检查点压缩后的摘要

EnvironmentEntry:
  id: str
  key: str
  value: str
  tags: list[str]
  visible_to: list[str]         # "all" 表示所有人可见

CampaignBackground:
  raw_input: str
  world_setting: str
  factions: list[dict]
  history: list[dict]
  important_locations: list[dict]
  initial_situation: str

CheckpointSummary:
  id: str
  stage_label: str
  summary_text: str
  character_updates: dict[str, dict]   # character_id -> {personality, notes}
  environment_snapshot: str
  timestamp: int

FortuneLevel:
  "great_auspicious" | "auspicious" | "normal" | "ominous" | "great_ominous"
```

### 模块 2: 解析器

**职责**：玩家输入格式解析（自然语言 → ActionUnit）和动作单元渲染（ActionUnit → 展示文本）。

**接口**：
- `parse_pc_input(text: str) -> ActionUnit` — 解析玩家输入为结构化动作单元
- `format_action_unit(au: ActionUnit, character_name: str) -> str` — 将动作单元渲染为可读文本
- `is_agent_directive(text: str) -> bool` — 判断是否为 Agent 指令
- `parse_agent_directive(text: str) -> (name: str, args: list[str])` — 解析指令名和参数

**输入格式规则**：
- `【】` 包裹 → 对话
- `（）` 包裹 → 内心活动
- 无包裹纯文本 → 行动
- `{}` 包裹 → Agent 指令（不写入动作单元）

### 模块 3: 骰子系统

**职责**：d20 骰子投点和技能检定计算。

**接口**：
- `roll_d20() -> DiceResult` — 投 1d20
- `check_skill(skill_modifier: int, dc: int) -> CheckResult` — 技能检定
- `roll_d100() -> int` — 投 d100（用于运势系统）

**检定规则**：
- 结果 = d20 + 技能加值
- 结果 >= DC → 成功；否则失败
- 自然 20 → 暴击（critical success）
- 自然 1 → 大失败（fumble）

### 模块 4: 运势系统

**职责**：NPC 行为倾向的随机性调节，通过 d100 投点映射到五级运势。

**接口**：
- `roll_fortune() -> FortuneLevel` — 投 d100 确定运势等级
- `fortune_prompt(level: FortuneLevel) -> str` — 根据运势等级生成提示词注入文本

**运势分档**：
- 95-100 → 大吉（great_auspicious）— 5%
- 75-94 → 吉（auspicious）— 20%
- 26-74 → 平（normal）— 49%
- 6-25 → 凶（ominous）— 20%
- 1-5 → 大凶（great_ominous）— 5%

**设计约束**：
- 运势只影响行为倾向（叙事层面的软调节），不直接决定成败
- 按检查点刷新，每个检查点周期内运势固定，避免短时间内大量波动

### 模块 5: 环境系统

**职责**：管理环境上下文（信息条目）和可见性过滤。

**接口**：
- `add_entry(key: str, value: str, tags: list[str], visible_to: list[str]) -> str` — 添加条目，返回 ID
- `update_entry(id: str, value: str) -> None` — 更新条目值
- `remove_entry(id: str) -> None` — 移除条目
- `entries_visible_to(character_id: str) -> list[EnvironmentEntry]` — 获取角色可见的所有条目
- `all_entries() -> list[EnvironmentEntry]` — 获取所有条目（全知视角用）
- `entries_by_tag(tag: str) -> list[EnvironmentEntry]` — 按标签查询

**常见条目类型（约定而非强制）**：时间、地点、天气、物品、氛围、状态、NPC

### 模块 6: 角色系统

**职责**：管理角色档案和角色上下文。

**接口**：
- `create_character(profile: CharacterProfile) -> None` — 创建角色
- `get_profile(character_id: str) -> CharacterProfile | None` — 获取角色档案
- `update_profile(character_id: str, updates: dict) -> None` — 更新角色档案
- `append_action_unit(character_id: str, au: ActionUnit) -> None` — 追加动作单元到角色上下文
- `get_context(character_id: str) -> CharacterContext | None` — 获取角色上下文
- `all_characters() -> list[CharacterProfile]` — 列出所有角色
- `create_npc_on_the_fly(name: str, world_context: str) -> CharacterProfile` — 运行时即时创建 NPC（调用 LLM）
- `archive_context(character_id: str, summary: str) -> None` — 归档上下文，用摘要替代

**设计约束**：
- 角色档案永不删除（即使角色离场）
- 上下文可在检查点时由玩家决定是否清理
- 新角色通过 entered 字段入场时自动创建完整档案

### 模块 7: 场景管理

**职责**：维护当前场景的在场人员列表，处理入场/离场。

**接口**：
- `present_characters() -> list[str]` — 获取当前在场角色 ID 列表
- `process_action_unit(au: ActionUnit) -> None` — 处理动作单元的 entered/left 字段
- `add_present(character_id: str) -> None` — 手动加入在场列表
- `remove_present(character_id: str) -> None` — 手动从在场列表移除
- `set_present(characters: list[str]) -> None` — 全量设置（用于一致性校验修正）

### 模块 8: 持久化

**职责**：游戏会话的序列化和反序列化，本地文件存储。

**接口**：
- `save_session(session: GameSession, path: str) -> None` — 保存到文件
- `load_session(path: str) -> GameSession` — 从文件加载
- `list_saves(directory: str) -> list[SaveInfo]` — 列出存档

**保存内容**：
- 战役背景
- 所有角色档案和角色上下文
- 环境上下文
- 检查点和摘要
- 在场人员列表
- 规则配置
- 运势状态（各角色当前运势）

**设计约束**：
- 使用 JSON 格式，人类可读
- 所有字段完整序列化/反序列化（无遗漏）
- 向后兼容（旧版本存档应能被新版本加载，缺失字段用默认值填充）

### 模块 9: 预设系统

**职责**：角色预设、世界观预设、模组的加载和管理。

**接口**：
- `list_character_presets() -> list[PresetInfo]` — 列出角色预设
- `load_character_preset(name_or_path: str) -> CharacterProfile` — 加载角色预设
- `list_world_presets() -> list[PresetInfo]` — 列出世界观预设
- `load_world_preset(name_or_path: str) -> CampaignBackground` — 加载世界观预设
- `list_modules() -> list[ModuleInfo]` — 列出模组
- `load_module(name_or_path: str) -> ModuleData` — 加载模组（世界观 + 初始角色 + 初始情境）

**目录结构**：
```
presets/
  characters/    # 角色预设
  worlds/        # 世界观预设
  modules/       # 完整模组
```

**设计约束**：
- 预设是跨战役可复用的，不属于任何特定模组
- 预设文件使用 JSON 格式
- 支持按名称查找（在预设目录下搜索）和按路径直接加载

### 模块 10: LLM 集成层

**职责**：封装所有 LLM 调用，提供结构化的输入输出接口。这是唯一直接和 LLM 交互的模块。

**接口**：
- `generate_npc_action(profile, context, dialogue_history, env_entries, present_list, fortune) -> ActionUnit`
- `generate_environment_action(env_context, present_list) -> ActionUnit`
- `judge_next_speaker(all_contexts, env, dialogue_history, present_list) -> JudgmentResult`
- `generate_summary(context_text) -> str`
- `create_npc_profile(name, world_context) -> CharacterProfile`
- `update_character_profiles(profiles, context_summary) -> dict[str, dict]`
- `generate_campaign_background(user_input) -> CampaignBackground`

**JSON 解析容错**：
- 每次 LLM 输出解析失败时，将错误信息反馈给 LLM 要求修正
- 最多重试 2 次（共 3 次尝试）
- 3 次均失败则抛出异常，由上层处理

**设计约束**：
- 所有 LLM 调用都通过本层，不允许其他模块直接调用 LLM
- 输入输出均为结构化数据（dataclass/dict），调用方无需关心 prompt 细节
- 支持不同的 LLM 后端（OpenAI 兼容接口），通过配置切换

### 模块 11: NPC 生成子系统

**职责**：协调角色上下文、环境、运势等信息，通过 LLM 生成 NPC 动作单元。

**接口**：
- `generate_npc_action(character_id: str) -> ActionUnit` — 生成指定 NPC 的下一个动作单元

**内部流程**：
1. 获取角色档案和角色上下文
2. 获取公开对话历史
3. 获取该角色可见的环境条目
4. 获取当前在场人员列表
5. 获取该角色当前运势等级
6. 组装 prompt，调用 LLM 集成层
7. 解析返回的 ActionUnit
8. 追加到角色上下文和对话日志

### 模块 12: 判断机制子系统

**职责**：判断下一个动作单元应由谁产生。

**接口**：
- `judge() -> JudgmentResult` — 判断下一个发言者
- `needs_sanity_check() -> bool` — 是否需要进行在场人员一致性校验（每 K 次一次）

**输出结构**：
```
JudgmentResult:
  next_speaker: str            # character_id 或 "environment"
  reason: str
  force_environment: bool
  corrected_present_characters: list[str] | None
```

**设计约束**：
- 判断结果是柔性建议，玩家可以打断
- 连续 N 个角色动作单元后必须插入环境动作单元（force_environment）
- 每 K 个动作单元进行一次在场人员一致性校验

### 模块 13: 检查点子系统

**职责**：管理检查点的触发、确认和执行。

**接口**：
- `propose_checkpoint(stage_label: str) -> CheckpointProposal` — Agent 提议检查点
- `confirm_checkpoint(proposal_id: str, clean_characters: list[str]) -> CheckpointSummary` — 玩家确认并执行
- `trigger_manually(stage_label: str) -> CheckpointProposal` — 玩家手动触发检查点

**检查点附带操作**：
1. 生成上下文摘要
2. 更新角色档案（需玩家确认重大变更）
3. 清理过期环境条目
4. 刷新所有在场 NPC 的运势
5. 玩家选择清理哪些离场角色的上下文

### 模块 14: 游戏循环（协调层）

**职责**：协调所有子系统，处理玩家输入，驱动整个游戏状态流转。这是最核心的协调模块，但本身不包含业务逻辑。

**核心状态**：
- `mode`: "player_present" | "player_absent"
- `rules_mode`: "pure_narrative" | "lightweight_rules"
- `pc_id`: str | None
- `session`: GameSession
- `judgment_counter`: int（用于在场人员一致性校验计数）
- `consecutive_character_actions`: int（用于强制环境插入计数）
- `pending_confirmation`: ConfirmationRequest | None（待玩家确认的操作）

**核心流程（玩家参与模式）**：
1. 接收玩家输入
2. 如果是 Agent 指令 → 分发到对应处理函数
3. 如果是 PC 动作单元 → 解析、追加到上下文、处理 entered/left
4. 运行判断机制，确定下一个发言者
5. 等待玩家 `{继续}` 或 `{到我}` 触发

**核心流程（玩家空缺模式）**：
1. 自动运行判断机制
2. 生成下一个动作单元（NPC 或环境）
3. 检查是否需要触发检查点/场景切换等需要确认的操作
4. 如果有待确认事项 → 暂停，等待玩家确认
5. 如果没有 → 继续自动推演
6. 到检查点时自动暂停

### 模块 15: CLI 界面

**职责**：命令行交互，接收用户输入，展示游戏内容。

**主要命令**：
- 游戏创建向导（new game）
- 加载存档（load）
- 列出存档（list saves）
- 游戏内交互循环
- Agent 指令解析与展示

**展示内容**：
- 动作单元（对话 + 行动 + 内心活动 + 角色名）
- 系统消息（检查点提示、确认请求等）
- 检定结果
- 角色档案面板
- 帮助信息

---

## Testing Decisions

### 测试原则

1. **测试外部行为，不测试实现细节** — 验证接口输入输出，不关心内部实现
2. **LLM 是黑盒，通过 Mock 做结构化测试** — 预设 JSON 输入输出，验证系统正确处理
3. **纯逻辑模块全覆盖** — 骰子、解析器、环境管理等纯逻辑模块必须有完整单元测试
4. **集成模块重点测流程** — 游戏循环等集成模块用 Mock 子系统的方式测状态流转

### 测试模块清单

| 模块 | 测试类型 | 测试重点 |
|------|---------|---------|
| 核心领域模型 | 单元测试 | 数据结构完整性、默认值、序列化/反序列化 |
| 解析器 | 单元测试 | 各种输入格式解析、边界情况、Agent 指令识别 |
| 骰子系统 | 单元测试 | d20 范围、检定计算、暴击/大失败、DC 边界 |
| 运势系统 | 单元测试 | d100 分档正确性、各等级映射、提示词生成 |
| 环境系统 | 单元测试 | 增删改查、可见性过滤、标签查询、边界情况 |
| 角色系统 | 单元测试 | 档案管理、上下文追加、归档、检索 |
| 场景管理 | 单元测试 | 入场/离场处理、列表维护、一致性校验接口 |
| 持久化 | 单元测试 | 保存/加载往返一致、所有字段完整、向后兼容 |
| 预设系统 | 单元测试 | 预设加载、列表查询、格式验证 |
| LLM 集成层 | Mock 测试 | JSON 解析容错、重试逻辑、prompt 组装验证 |
| 判断机制子系统 | Mock 测试 | 输出解析、在场人员修正、强制环境插入 |
| 检查点子系统 | Mock 测试 | 提议/确认流程、摘要生成、角色档案更新 |
| NPC 生成子系统 | Mock 测试 | 运势注入、上下文组装、动作单元追加 |
| 游戏循环 | 集成测试 + Mock | 状态流转、双模式行为、玩家确认原则 |

### 测试技术

- 测试框架：pytest（与现有项目一致）
- LLM Mock：通过注入 mock LLM provider，返回预设 JSON
- 随机数控制：骰子和运势测试时使用固定种子确保可重复

---

## Out of Scope

以下内容明确不在 v1 范围内，可能在未来版本中考虑：

1. **多玩家/多 PC** — v1 专注单玩家单 PC 体验
2. **完整规则引擎** — v1 只有轻量 d20 检定，不包含战斗轮、伤害计算、状态追踪等
3. **动作单元细粒度受众** — v1 中 audience 作用于整个动作单元，不分对话/行动/内心活动
4. **动态感知条件** — v1 只有静态可见角色列表，不支持距离、感官类型等动态感知
5. **AI 生成预设** — v1 支持预设的导入和使用，但不包含 AI 自动生成预设的功能
6. **GUI 界面** — v1 只有 CLI 界面，GUI 作为未来方向
7. **网络多人** — v1 是纯本地单玩家应用
8. **语音交互** — v1 只有文字交互
9. **图像生成** — v1 不包含场景插图、角色立绘等 AI 图像生成
10. **模组编辑器** — v1 可以使用预设和模组，但不提供可视化的模组编辑工具

---

## Further Notes

### 相关 ADR

- **ADR-0001**: 角色动作单元作为第一公民 — 动作单元是叙事的基本单位
- **ADR-0002**: 统一采用 d20 骰子系统 — 移除多系统架构，简化为单一 d20 roll-over
- **ADR-0003**: NPC 侧采用运势系统而非骰子检定 — PC/NPC 两侧采用不同随机性机制

### 术语一致性

所有用户可见文本和代码中的命名必须与 CONTEXT.md 术语表一致。核心术语：
- 动作单元 (Action Unit)
- 角色档案 (Character Profile)
- 角色上下文 (Character Context)
- 检查点 (Checkpoint)
- 运势 (Fortune)
- 难度等级 (DC — Difficulty Class)
- 玩家参与模式 / 玩家空缺模式
- 预设 (Preset) / 模组 (Module)
- Agent 指令 (Agent Directive)
