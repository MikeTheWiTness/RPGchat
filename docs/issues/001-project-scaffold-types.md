# Issue #1: 项目脚手架 + 核心类型定义

## What to build

搭建项目基础结构和所有核心 TypeScript 类型/接口定义。

- 初始化项目：包管理器、TypeScript 配置、测试框架配置
- 定义所有核心数据类型（含完整字段注释）：
  - `ActionUnit`：动作单元统一 JSON 结构
  - `JudgmentResult`：判断机制输出结构
  - `CharacterProfile`：角色档案结构
  - `CharacterContext`：角色上下文结构（动作单元历史）
  - `EnvironmentEntry`：环境信息条目结构
  - `SceneState`：场景状态（在场人员列表）
  - `CheckpointSummary`：检查点摘要结构
  - `GameSession`：游戏会话顶层结构
  - `DiceRollResult` / `CheckResult`：骰子相关类型
- 确保所有类型在后续模块中直接引用，无需重复定义

## Acceptance criteria

- [ ] 项目可通过 `npm install` 安装依赖
- [ ] TypeScript 编译通过（`tsc --noEmit`）
- [ ] 测试框架可运行（哪怕没有测试用例）
- [ ] 所有核心类型/接口定义在单独的类型文件中，包含 JSDoc 注释
- [ ] `ActionUnit` 接口包含所有字段：`character_id`、`dialogue`、`action`、`inner_thought`、`audience`、`entered`、`left`
- [ ] `JudgmentResult` 接口包含所有字段：`next_speaker`、`reason`、`force_environment`、`corrected_present_characters`
- [ ] `GameSession` 接口包含：`campaign_background`、`characters`、`environment_entries`、`dialogue_log`、`scene_state`、`checkpoints`、`mode`、`rules_config`

## Blocked by

None — can start immediately
