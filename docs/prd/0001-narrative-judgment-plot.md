# PRD: Narrative 统一输出 & 判断机制增强 & 剧情事件追踪

**日期**: 2026-06-26
**状态**: Draft
**关联 ADR**: [ADR-0004](../docs/adr/0004-narrative-unified-output.md)

---

## Problem Statement

TRPG Chat Agent 的 LLM 输出机制存在以下问题：

1. **NP会C 三段式输出割裂**：LLM 分别输出 `dialogue`、`action`、`inner_thought` 三个字段，导致对话和行动缺乏自然的叙事衔接，并且每次有 action 就需要额外的「动作结果轮」LLM 调用
2. **环境介入缺乏意图控制**：判断机制选环境时只给一个 reason 字符串，环境 LLM 无法区分是烘托气氛还是打破僵局，导致环境倾向于戏剧化
3. **剧情推进无追踪**：模组中的关键事件和线索没有程序化追踪，全靠玩家手动 `{设定大纲}`
4. **场景切换无自动触发**：场景切换完全依赖玩家手动指令
5. **回滚机制不完整**：快照缺少角色档案和战役背景字段，回滚时动态创建的 NPC 不会撤销
6. **检查点功能空壳**：只更新了运势，角色档案更新和上下文压缩未实现
7. **持久化覆盖不全**：`plot_outline`、`director_intents` 不写入存档

## Solution

1. NPC/环境 LLM 统一输出 `narrative` 字段（连贯中文叙述），程序通过 `split_narrative()` 按标点标记拆解为 ActionUnit
2. 判断机制增加 `env_intent`（atmosphere/break/transition）、`proposed_scene_change`、`completed_events`、`discovered_clues`
3. 剧情事件三层兜底追踪
4. 检查点完整实现（角色档案 LLM 更新、剧情事件复核、上下文压缩）
5. 快照回滚机制补全

## User Stories

1. As a 玩家, I want NPC 输出的对话和行动更自然连贯，so that 叙事读起来像小说而非指令列表
2. As a 玩家, I want 环境描述不会无端插入戏剧性事件，so that 气氛描写和剧情推进能分开控制
3. As a 玩家-空缺模式, I want 自动推演能追踪剧情事件的完成状态，so that 故事有结构化的推进感
4. As a 玩家, I want 能通过 `{回滚 N}` 回到任意历史点并重新推演，so that 不满意的剧情分支可以被撤销
5. As a 玩家, I want 场景切换时系统自动弹出确认，so that 我不会错过重要的叙事转折
6. As a 玩家, I want 存档加载后不丢失剧情大纲和导演意图，so that 长会话的推力不被中断
7. As a 玩家, I want 用 `{调查 描述}` 定向询问 GM 某个动作的结果，so that 我不需要为每个动作触发一次浪费的 LLM 调用
8. As a 玩家, I want PC 输入时可以用 `"..."` 标记对话（替代 `【】`），so that 输入更自然

## Implementation Decisions

### 1. Narrative 统一输出

**NPC 输出格式变更**：

```json
{
  "character_id": "npc_xxx",
  "narrative": "佐佐木站起身\"该出发了\"（希望别下雨）拿起外套走向门口",
  "event_flags": {"completed": ["meeting_start"], "clues": ["boss_location"]},
  "audience": null,
  "entered": null,
  "left": null
}
```

`split_narrative()` 将其切分为 3 个 ActionUnit（action + dialogue + inner_thought），共享同一 `_seq` 和一次快照。

**环境输出格式变更**：环境也输出 `narrative`，但环境 narrative **不切分**——`（）` `""` 可能是拟声词或注释（如「奥术飞弹（1环）」），直接作为 action 原文展示。

### 2. 判断机制增强

`JudgmentResult` 增加字段：

```
env_intent: "atmosphere" | "break" | "transition" | None
proposed_scene_change: str | None
completed_events: list[str] | None
discovered_clues: list[str] | None
```

**env_intent 行为指南**（注入判断 prompt）：
- `atmosphere` → 环境只写感官细节，禁止新事件/人物
- `break` → 环境可引入外部事件，不新人物
- `transition` → 另输出 `proposed_scene_change`，触发切换确认

**泊松随机交互**：泊松随机仍负责决定「是否强制环境轮」，但结果告知判断 LLM（`force_env_check=true`），LLM 自决 `env_intent`。移除 `consecutive_env_count` 和「环境最多连续 4 轮」硬限制。

### 3. 剧情事件追踪

三层兜底：

| 层 | 谁 | 何时 | 权威性 |
|----|----|------|--------|
| 软标记 | NPC LLM | 每次 narrative 生成 | 非权威 |
| 权威判定 | 判断 LLM | 每次 judge | 主要来源 |
| 长程复核 | 检查点 LLM | 检查点 | 兜底 |

判断 prompt 中注入 NPC 软标记 + PlotTracker 的待办事件列表，LLM 综合判定 `completed_events` 和 `discovered_clues`。

### 4. 场景切换流程

```
判断 LLM 输出 proposed_scene_change →
  ConfirmationManager.propose(SCENE_CHANGE, ...) →
    玩家 {确认} →
      触发检查点 →
      判断决定 new_present_characters →
      环境 LLM 生成新场景开场 narrative
```

### 5. 检查点重新设计

检查点触发时执行（顺序）：
1. **摘要生成**：LLM 总结阶段叙事
2. **角色档案更新**：LLM 评估各角色 personality/relationships/skills 变化
3. **剧情事件复核**：LLM 回顾阶段叙事，确认/补标 completed_events 和 discovered_clues
4. **运势刷新**：每个在场 NPC 独立投 d100
5. **上下文压缩**：用摘要替代旧动作单元，保留摘要归档
6. **环境条目清理**：保留最近 5 条，追加检查点摘要条目

### 6. 快照回滚补全

Snapshot 需增加：
- `characters`：角色档案字典（回滚时撤销动态创建的 NPC）
- `campaign_background`：战役背景（防止场景切换中的背景变更残留）

`_restore_snapshot()` 需同时恢复这两个字段。

### 7. 持久化覆盖

`persistence.py` 的 save/load 需要处理：
- `plot_outline`（含嵌套的 PlotChapter/PlotEvent）
- `director_intents`

`_deserialize_session` 需增加 `_make_plot_outline()` 等反序列化函数。

### 8. PC 输入扩展

`parse_pc_input()` 同时接受 `""...""`（及变体）作为对话标记。`【】` 保留作为备选。优先级：`【】` 先提取，然后 `""` 补齐。

### 9. {调查} 指令

新指令 `{调查 描述}`，内容传给环境/场景叙述者 LLM 作为定向查询，返回仅 action 字段的结果。替代旧的自动 PC 动作结果轮。移除 `generate_pc_action_result()`。

### 10. 环境连续轮限制移除

删除 `consecutive_env_count` 变量、`_roll_force_env()` 中的 `force_character` 分支和相关硬限制逻辑。

---

## Testing Decisions

### 测试原则
- 测试只验证外部行为，不测试实现细节
- 测试必须代表真实使用场景，不为了通过率削减需求
- 禁止道德审查内容

### 优先测试的模块

| 模块 | 测试重点 | 现有测试文件 |
|------|----------|-------------|
| `parser.py` | `split_narrative()` 多引号支持、PC 输入双格式、`{调查}` 指令识别 | `test_parser.py` |
| `judgment.py` | `env_intent`、`proposed_scene_change`、`completed_events` 字段 | `test_judgment.py` |
| `game_loop.py` | 场景切换流程、剧情事件更新、快照回滚完整性 | `test_game_loop.py`、`test_e2e.py` |
| `checkpoint.py` | 角色档案 LLM 更新、事件复核、压缩 | `test_checkpoint.py` |
| `persistence.py` | `plot_outline`/`director_intents` 序列化往返 | `test_persistence.py` |
| `plot_tracker.py` | 事件完成/线索发现/章节推进 | `test_plot_tracker.py`（新建） |

### 测试风格
遵循现有测试模式——使用 `MockLLMProvider` 注入预设响应，验证系统行为而非 LLM 行为。测试不应因为 LLM 格式变更而脆弱。

---

## Out of Scope

- GUI 版本的确认按钮（当前仅 CLI `{确认}`/`{拒绝}`）
- 按字段细粒度控制受众（`dialogue_audience`、`action_audience` 等）
- 感知条件覆写（距离、感官类型等）
- `{调查}` 的批量查询（一次调查多个事物）
- 多玩家/多 PC 支持
- 完整规则引擎（战斗轮、伤害计算等）
- 输入体验优化（指令智預能测、自动补齐等）

---

## Further Notes

- `narrative` 格式已通过 ADR-0004 确认，符合 CONTEXT.md 域模型
- 所有变更需反映到 CONTEXT.md（Grill 时已部分更新）
- 移除的环境硬限制逻辑需要清理相关测试 fixture
- `consecutive_env_count` 从 `SceneState` 移除但保留在 snapshot 中向后兼容
