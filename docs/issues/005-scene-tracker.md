# Issue #5: 场景在场人员追踪 (SceneTracker)

## What to build

实现场景在场人员列表的维护模块。

- 维护一个全局的 `present_characters` 列表（角色 ID 集合）
- `process_action_unit(au: ActionUnit)` — 处理动作单元：
  - 若 `au.entered` 有值，将其中角色 ID 加入在场列表
  - 若 `au.left` 有值，将其中角色 ID 从在场列表中移除
  - 返回更新后的在场列表
- `resolve_audience(au: ActionUnit)` — 解析实际受众：
  - 若 `au.audience` 有值 → 返回 `audience` ∩ `present_characters`（只减不增）
  - 若 `au.audience` 为 null → 返回 `present_characters`（全部在场人员）
  - 若 `au.audience` 中包含不在场人员 → 报错/警告
- `get_present()` — 获取当前在场列表
- `apply_correction(corrected_list)` — 接受判断机制的一致性校验修正

## Acceptance criteria

- [ ] 入场：`entered: ["npc_2"]` → present_characters 增加 npc_2
- [ ] 离场：`left: ["npc_1"]` → present_characters 移除 npc_1
- [ ] 默认受众 = 当前在场列表
- [ ] `audience` 限定后正确缩小范围
- [ ] `audience` 包含不在场角色时报错
- [ ] 一致性修正覆盖当前列表
- [ ] 单元测试覆盖入场、离场、受众解析、一致性修正

## Blocked by

- #1 — 核心类型定义
- #3 — 角色存储（需要验证 character_id 有效性）
