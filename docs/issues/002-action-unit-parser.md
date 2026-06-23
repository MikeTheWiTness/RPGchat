# Issue #2: PC 输入解析器 (ActionUnitParser)

## What to build

实现 PC 输入文本的解析器，将玩家输入的自然格式文本转换为标准的 `ActionUnit` JSON。

- 解析规则：
  - `""` 包裹 → `dialogue` 字段
  - `（）` 包裹 → `inner_thought` 字段
  - 无包裹纯文本 → `action` 字段
  - `{}` 包裹 → 提取为 Agent 指令（`AgentDirective`），不在 `ActionUnit` 中，单独返回
- 支持各种组合：仅有对话、仅有行动、三者都有、三者都没有（报错）
- 支持嵌套/混合场景：`我走过去"你好"（他看起来很紧张）` 应正确解析
- 实现 JSON 验证/重试逻辑：接收 LLM 返回的 JSON 字符串，尝试解析，失败时返回错误信息（最多重试 2 次的逻辑在 LLMGateway 层调用此方法）

## Acceptance criteria

- [ ] `"小心身后"` → dialogue="小心身后"，其余为 null
- [ ] `我拿起长剑砍去` → action="我拿起长剑砍去"，其余为 null
- [ ] `（心里非常紧张）` → inner_thought="心里非常紧张"，其余为 null
- [ ] `我拿起剑"小心身后"（紧张）{继续}` → action/dialogue/inner_thought 正确 + 返回 AgentDirective
- [ ] 空字符串输入报错
- [ ] 非法 JSON 字符串被检测，返回解析错误信息
- [ ] 合法 JSON 字符串正确解析为 ActionUnit
- [ ] 单元测试覆盖以上所有场景

## Blocked by

- #1 — 核心类型定义
