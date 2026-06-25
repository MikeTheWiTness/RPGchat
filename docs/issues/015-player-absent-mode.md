# Issue #15: 玩家空缺模式

## What to build

实现全自动剧情推演模式。

- `start_auto_mode(session, pause_interval?)` — 切换到玩家空缺模式
  - 不创建 PC，所有角色由 Agent 控制
  - 判断机制持续自动运行，每轮自动生成 NPC/环境动作单元
  - `pause_interval`：每 N 个动作单元自动暂停（null = 不停，直到章节结束或用户手动暂停）
- `pause_auto_mode()` — 暂停自动推演
- `resume_auto_mode()` — 继续自动推演
- 在自动模式下玩家仍可通过 `{}` Agent 指令干预（如 `{让战斗更加激烈}`、`{主角应该受伤}`）
- CLI 界面适配：自动模式下显示"自动推演中..."状态，暂停时允许输入指令
- 自动暂停条件可配置：按 N 个动作单元、按章节结束、按检查点触发

## Acceptance criteria

- [ ] 切换到玩家空缺模式后自动推进
- [ ] pause_interval=N 时每 N 步自动暂停
- [ ] 暂停时 `{}` 指令可正常下发
- [ ] 暂停后可继续推演
- [ ] 自动模式下剧情质量不低于手动模式（无明显崩溃）
- [ ] CLI 界面正确显示自动模式状态
- [ ] 集成测试覆盖自动推演→暂停→继续完整流程

## Blocked by

- #11 — GameLoop + CLI
