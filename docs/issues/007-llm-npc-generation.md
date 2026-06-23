# Issue #7: LLM 集成 — NPC 动作单元生成

## What to build

实现 LLM Gateway 的 NPC 动作单元生成调用。

- 创建统一的 LLM API 抽象层（支持切换不同的 LLM 提供商）
- `generate_npc_action_unit(character_id)` — 为指定 NPC 生成动作单元：
  1. 调用 `ContextAssembler.assemble_for_character(character_id)` 获取上下文
  2. 构建 NPC 生成 prompt，要求 LLM 返回符合 `ActionUnit` JSON 格式的内容
  3. 调用 LLM API
  4. 调用 `ActionUnitParser` 验证返回的 JSON，解析失败时重试最多 2 次
  5. 返回解析成功的 `ActionUnit`
- `create_npc_profile(name, context_description)` — 运行时即时创建 NPC 档案：
  1. 基于战役背景 + 当前场景上下文，调用 LLM 生成新 NPC 的角色档案（姓名、性格、外貌、动机等）
  2. 返回 `CharacterProfile`，由上层写入 CharacterStore
- LLM 配置通过环境变量/配置文件管理（API key、模型名称、endpoint）

## Acceptance criteria

- [ ] NPC 动作单元生成返回合法的 ActionUnit JSON
- [ ] ActionUnit 中 dialogue/action/inner_thought 至少一项不为空
- [ ] JSON 解析失败时重试最多 2 次，仍失败则抛出错误
- [ ] 即时创建 NPC 返回包含姓名、性格、外貌描述的 CharacterProfile
- [ ] LLM API 配置可切换（通过环境变量）
- [ ] 集成测试覆盖：模拟 LLM 返回合法/非法 JSON 的场景

## Blocked by

- #2 — ActionUnitParser（JSON 验证）
- #6 — ContextAssembler（上下文组装）
