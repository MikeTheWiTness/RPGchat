# Issue #8: LLM 集成 — 判断机制 + 环境生成

## What to build

在 LLM Gateway 中实现判断机制和环境动作单元的生成调用。

- `judge_next_speaker(action_count_since_env, present_characters)` — 判断接下来谁发言：
  1. 调用 `ContextAssembler.assemble_for_judgment()` 获取全知上下文
  2. 若连续角色动作单元数 >= N（可配置），prompt 中标记 `force_environment: true`
  3. 若距离上次一致性校验 >= K 个动作单元，prompt 中要求附带 `corrected_present_characters`
  4. 调用 LLM API，要求返回 `JudgmentResult` JSON
  5. 验证 JSON（含重试逻辑）
- `generate_environment_action_unit()` — 生成环境动作单元：
  1. 类似 NPC 生成，但 `character_id` 为 null，仅 `action` 字段有意义
  2. 环境动作单元也应包含 `entered`/`left` 字段（新角色出场/旧角色退场）
- 配置项：`MAX_CONSECUTIVE_CHARACTERS`（默认 5）、`SANITY_CHECK_INTERVAL`（默认 10）

## Acceptance criteria

- [ ] 判断机制返回合法的 JudgmentResult（next_speaker、reason、force_environment、corrected_present_characters）
- [ ] 连续角色动作单元数 >= N 时 force_environment 为 true，next_speaker 为 "environment"
- [ ] 第 K 个动作单元时返回 corrected_present_characters
- [ ] 非校验轮次 corrected_present_characters 为 null
- [ ] 环境动作单元返回合法 ActionUnit（character_id 为 null）
- [ ] 集成测试覆盖判断机制和环境生成的正常/边界场景

## Blocked by

- #6 — ContextAssembler
- #7 — LLM Gateway 基础（LLM 调用层复用）
