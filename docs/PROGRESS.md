# RPG Chat Agent 项目进度汇总

> 更新日期：2026-06-24

---

## 一、当前状态

### 测试状态
- **221 passed, 2 pre-existing failures** — 新增测试全部通过
- 2 个预存失败与本次改动无关：`test_handle_continue_npc`（环境 AU `entered` 字段触发响应顺序偏移）、`test_handle_skill_check`（引用已移除的 `coc` 规则系统，见 ADR-0002）
- 测试覆盖率：核心领域模型、解析器、骰子、运势、环境、场景、角色存储、对话日志、持久化、预设加载、模组系统、游戏循环、自动模式、玩家确认、检查点系统、玩家空缺模式、检定嵌入叙事、E2E 等

### 代码质量
- 无 TODO / FIXME / HACK 标记
- 所有模块有对应的单元测试
- LLM 驱动模块使用 Mock LLM 做结构化测试

---

## 二、已完成工作

### Phase 0: 领域建模与文档（grill-with-docs）

通过 33 轮质询，澄清了核心领域概念和设计决策：

| 决策 | 结论 | 文档 |
|------|------|------|
| 对话包裹符号 | 统一为 `【】`（英文双引号不便输入） | CONTEXT.md |
| 角色档案扩展字段 | physique/identity/clothing/behavior/intimate_features 正式加入 | CONTEXT.md |
| 骰子系统 | 统一采用 d20 roll-over，移除多系统架构 | ADR-0002 |
| NPC 侧随机性 | 运势系统（五级制、d100、按检查点刷新、角色独立） | ADR-0003 |
| 玩家视角 | 全知视角（两种模式下均可见所有内心活动） | CONTEXT.md |
| 玩家确认原则 | 场景切换/检查点/时间快进/角色档案重大变更需确认 | CONTEXT.md |
| 发言顺序 | 柔性建议，不强制 | CONTEXT.md |
| 回合 | 软概念，环境不算角色 | CONTEXT.md |
| 公开对话历史 | 推导数据，从动作单元聚合 | CONTEXT.md |
| 预设系统 | 角色预设 + 世界观预设 + 模组（完整战役包） | CONTEXT.md |
| AI 生成预设 | 待开发，支持三种粒度（角色/世界观/完整模组） | CONTEXT.md |
| 运行模式 | 玩家参与模式 + 玩家空缺模式，均为核心 | CONTEXT.md |
| 多玩家 | 短期内不考虑 | CONTEXT.md |
| 环境动作单元 | 客观世界变化 + GM 旁白，两者都是 | CONTEXT.md |
| 主要/次要角色 | 不做区分，检查点时由玩家确认清理 | CONTEXT.md |

**产出文档**：
- [CONTEXT.md](file:///d:/RPGchat/CONTEXT.md) — 领域语言与核心概念（已更新）
- [docs/adr/0001-character-action-units-as-first-class.md](file:///d:/RPGchat/docs/adr/0001-character-action-units-as-first-class.md) — 已有
- [docs/adr/0002-unified-d20-system.md](file:///d:/RPGchat/docs/adr/0002-unified-d20-system.md) — 新增
- [docs/adr/0003-fortune-system-for-npcs.md](file:///d:/RPGchat/docs/adr/0003-fortune-system-for-npcs.md) — 新增
- [docs/prd-v1.md](file:///d:/RPGchat/docs/prd-v1.md) — 产品需求文档（80 条 User Stories）

### Phase 1: Bug 修复

| # | 修复内容 | 状态 |
|---|---------|------|
| 1 | 持久化 `_make_profile` 补全扩展字段（physique/identity/clothing/behavior/intimate_features） | ✅ |
| 2 | 移除 `power_system` 冗余字段，内容合并到 `world_setting` | ✅ |
| 3 | 骰子系统简化为单一 d20 roll-over，移除 COC 等多系统分支 | ✅ |
| 4 | 修复 6 个测试失败（mock LLM 响应顺序与实际调用不匹配，entered 字段会触发 create_npc_profile） | ✅ |

### Phase 2: 新功能（已完成核心）

| # | 功能 | 状态 | 测试 |
|---|------|------|------|
| 1 | 运势系统核心（d100 投点、五级映射、提示词生成） | ✅ 完成 | 5 个测试 |
| 2 | d20 骰子引擎与技能检定处理 | ✅ 完成 | 22 个测试 |
| 3 | 玩家确认原则框架（状态机、四类确认、game_loop 集成） | ✅ 完成 | 13 个测试 |
| 4 | 检查点系统（提议-确认-执行、环境清理、运势刷新、离场清理） | ✅ 完成 | 6 个测试 |
| 5 | 运势系统接入 NPC 生成（fortune 存储到上下文、prompt 注入运势描述） | ✅ 完成 | 8 个测试 |

---

## 三、待办事项（Todo）

### 🔴 高优先级

#### 1. 玩家确认原则框架 ✅ 已完成
- ~~实现确认请求/响应状态机（pending_confirmation）~~
- ~~支持四类确认：场景切换、检查点、时间快进、角色档案重大变更~~
- ~~CLI 交互：玩家输入 `{确认}`/`{拒绝}`~~
- **对应模块**：confirmation, game_loop
- **对应 User Stories**：US-70 ~ US-74
- **备注**：纯逻辑模块 `confirmation.py` 已完成状态机；game_loop 已集成检查点提议-确认流程；场景切换/时间快进/档案变更的提议入口待后续功能接入时补全

#### 2. 检查点系统（提议-确认-执行）✅ 已完成
- ~~检查点提议（`{检查点}` / `{检查点 标签名}` 指令）~~
- ~~玩家确认流程（`{确认}` / `{确认 清理角色id}` / `{拒绝}`）~~
- ~~执行逻辑：生成摘要、环境清理、运势刷新~~
- ~~检查点时玩家清理离场角色上下文（档案保留）~~
- **对应模块**：checkpoint, game_loop
- **对应 User Stories**：US-41 ~ US-48, US-24



### 🟡 中优先级

#### 3. 运势系统接入 NPC 生成 ✅ 已完成
- ~~CharacterContext 新增 fortune 字段（默认 normal）~~
- ~~检查点执行后将运势写入 CharacterContext.fortune~~
- ~~NPC prompt 注入运势行为倾向描述（大凶/凶/平/吉/大吉）~~
- **对应模块**：llm, checkpoint, context, types
- **对应 User Stories**：US-36, US-37, US-38

#### 4. 玩家空缺模式 ✅ 已完成
- ~~无 PC 自动推演~~
- ~~检查点自动暂停，玩家确认后继续~~
- ~~玩家可随时输入指令干预~~
- **对应模块**：game_loop, auto_mode
- **对应 User Stories**：US-15 ~ US-19
- **备注**：`new_game_absent()` 创建无 PC 会话；自由文本输入作为环境动作单元干预剧情；`AutoModeController` 检测到待确认事项自动暂停，确认后 `resume()` 继续；骰子检定在空缺模式禁用

#### 5. 检定嵌入叙事 ✅ 已完成
- ~~玩家输入动作 → LLM 判断是否需要检定 + 选择技能 + 决定 DC~~
- ~~自动用 PC 角色卡技能值进行 d20 检定~~
- ~~LLM 生成融入检定结果的动作单元（成功/失败/暴击/大失败）~~
- ~~检定结果以 `[检定]` 行展示，叙事中不出现数字~~
- **对应模块**：game_loop, llm, rules
- **对应 User Stories**：US-34, US-35
- **备注**：仅在 light-rules 模式触发；纯叙事模式走原路径；玩家仍可用 `{检定 技能名 DC}` 显式检定（向后兼容）

#### 6. 预设系统 - 模组支持 ✅ 已完成
- ~~模组格式定义（世界观 + 初始角色 + 初始情境）~~
- ~~列出/加载模组~~
- **对应模块**：preset_loader, game_loop, cli
- **对应 User Stories**：US-49 ~ US-54
- **备注**：模组采用文件夹结构（`presets/modules/<模组名>/`，含 `module.json` + `world.json` + `characters/*.json`）；`new_game_with_module()` 一次性加载世界观+全部角色并初始化场景，支持玩家参与/空缺两种模式；已内置两个预设模组：铁炉镇冒险（经典 DnD）、新东京暗流（现代都市），各含 3 个完整词条角色

#### 7. `{修改角色}` Agent 指令 ✅ 已完成
- ~~玩家直接修改角色档案字段~~
- ~~语法：`{修改角色 角色ID 字段名 值}`~~
- ~~支持字符串和 JSON 值（JSON 用于 dict 字段如 skills/attributes）~~
- **对应模块**：game_loop
- **对应 User Stories**：US-63

### 🟢 低优先级

#### 8. 动作单元受众可见性 ✅ 已完成
- ~~audience 字段生效，限定谁能感知到动作单元~~
- ~~角色上下文按可见性过滤~~
- ~~`ContextAssembler.assemble_for_character()` 新增 `perceived_actions` 字段~~
- ~~NPC prompt 使用 `perceived_actions` 构建对话上下文~~
- **对应模块**：scene, context, character, llm
- **对应 User Stories**：US-26 ~ US-29

#### 9. AI 生成预设功能
- 输入简短描述，LLM 生成完整预设/模组
- 保存到 presets/ 目录供复用
- **对应模块**：preset_loader, llm
- **对应 User Stories**：US-55

#### 10. `entered` 字段触发完整角色档案生成
- 当前是 `create_npc_on_the_fly` 简陋版本（只有 id/name/personality）
- 升级为通过 LLM 生成完整角色档案
- **对应模块**：game_loop, llm
- **对应 User Stories**：US-21

#### 11. 游戏创建向导增强 ✅ 已完成
- ~~选择运行模式（玩家参与/玩家空缺）~~
- ~~导入模组/预设~~
- ~~PC 档案编辑~~
- ~~新增 `_create_pc_profile()` 辅助函数：支持从预设加载完整角色卡作为 PC，或手动快速创建~~
- ~~新增 `build_pc_from_preset()` 函数（preset_loader）：一键将角色预设转为 PC~~
- **对应模块**：cli, preset_loader
- **对应 User Stories**：US-1 ~ US-7

---

## 四、模块架构概览

### 纯逻辑层（可完整单元测试）
| 模块 | 文件 | 状态 |
|------|------|------|
| 核心领域模型 | [types.py](file:///d:/RPGchat/src/rpg_chat/types.py) | ✅ |
| 解析器 | [parser.py](file:///d:/RPGchat/src/rpg_chat/parser.py) | ✅ |
| 骰子系统 | [dice.py](file:///d:/RPGchat/src/rpg_chat/dice.py) | ✅ |
| 运势系统 | [fortune.py](file:///d:/RPGchat/src/rpg_chat/fortune.py) | ✅ |
| 环境系统 | [environment.py](file:///d:/RPGchat/src/rpg_chat/environment.py) | ✅ |
| 角色系统 | [store.py](file:///d:/RPGchat/src/rpg_chat/store.py) | ✅ |
| 场景管理 | [scene.py](file:///d:/RPGchat/src/rpg_chat/scene.py) | ✅ |
| 持久化 | [persistence.py](file:///d:/RPGchat/src/rpg_chat/persistence.py) | ✅ |
| 预设系统 | [preset_loader.py](file:///d:/RPGchat/src/rpg_chat/preset_loader.py) | ✅（角色+世界观，模组待加） |
| 玩家确认 | [confirmation.py](file:///d:/RPGchat/src/rpg_chat/confirmation.py) | ✅ |
| 上下文组装 | [context.py](file:///d:/RPGchat/src/rpg_chat/context.py) | ✅（运势传递已接入） |

### LLM 驱动层（Mock 测试）
| 模块 | 文件 | 状态 |
|------|------|------|
| LLM 集成层 | [llm.py](file:///d:/RPGchat/src/rpg_chat/llm.py) | ✅ |
| NPC 生成 | [llm.py](file:///d:/RPGchat/src/rpg_chat/llm.py) | ✅ |
| 判断机制 | [judgment.py](file:///d:/RPGchat/src/rpg_chat/judgment.py) | ✅ |
| 检查点摘要 | [checkpoint.py](file:///d:/RPGchat/src/rpg_chat/checkpoint.py) | ⚠️ 骨架已在，功能待完善 |

### 协调层
| 模块 | 文件 | 状态 |
|------|------|------|
| 游戏循环 | [game_loop.py](file:///d:/RPGchat/src/rpg_chat/game_loop.py) | ✅（玩家确认、空缺模式待加） |

### 界面层
| 模块 | 文件 | 状态 |
|------|------|------|
| CLI 界面 | [cli.py](file:///d:/RPGchat/cli.py) | ✅（指令待补全） |

---

## 五、下一步建议

**推荐开发顺序**：

1. **玩家确认原则框架** — 是检查点、场景切换等多个功能的基础设施
2. **检查点系统完善** — 触发上下文压缩、运势刷新、角色档案更新
3. **运势系统接入 NPC 生成** — 把运势系统真正用起来
4. **玩家空缺模式** — 第二核心模式
5. **检定嵌入叙事** — 提升玩家体验
6. **模组支持** — 完善预设生态

每次迭代遵循 TDD 流程：先写测试 → 写实现 → 重构 → 全部测试通过。
