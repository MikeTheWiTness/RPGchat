# Issue #9: 骰子引擎 (DiceEngine)

## What to build

实现可插拔的骰子检定模块。

- `roll(expression)` — 执行骰子表达式：
  - 支持格式：`d100`、`3d6`、`d20`、`2d6+3` 等标准骰子表达式
  - 返回：`{ expression, rolls: number[], modifier, total }`
- `check(skill_name, character_id, difficulty)` — 技能检定：
  - 从角色档案读取技能值
  - 根据规则配置确定骰子表达式（COC 用 d100、D&D 用 d20）
  - 执行 roll，比较结果与技能值/difficulty
  - 返回：`{ success, critical, fumble, roll: DiceRollResult, skill_value, result_description }`
- 规则配置支持：通过 JSON 配置文件定义技能列表、属性映射、检定公式。后续 Issue #12 集成完整规则，此 Issue 只需数据结构 + 核心骰子逻辑

## Acceptance criteria

- [ ] `d100` 返回 1-100 之间的随机整数
- [ ] `3d6` 返回 3-18 之间的值
- [ ] `2d6+3` 正确计算（2 个 d6 之和 + 3）
- [ ] 技能检定：COC 模式下 d100 <= 技能值 → 成功
- [ ] 技能检定：D&D 模式下 d20 + 调整值 >= difficulty → 成功
- [ ] 大成功/大失败检测（d100: 01 大成功，100 大失败；d20: 20 大成功，1 大失败）
- [ ] 规则配置正确加载和切换
- [ ] 单元测试覆盖骰子表达式解析和检定逻辑

## Blocked by

- #1 — 核心类型定义
