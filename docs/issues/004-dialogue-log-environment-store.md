# Issue #4: 对话日志 + 环境存储 (DialogueLog + EnvironmentStore)

## What to build

实现两个独立的存储模块：

### DialogueLog
- 追加式公开对话历史，按时序存储所有动作单元的 `dialogue` 字段（含 `character_id` 和时间戳）
- `append(character_id, dialogue)` — 追加一条对话
- `history()` — 获取完整时序列表
- NPC 发出空 dialogue（纯行动/内心活动）时不追加

### EnvironmentStore
- 管理环境信息条目，每条包含：描述内容 + `visible_to` 角色 ID 列表
- `add_entry(description, visible_to)` — 添加环境信息
- `visible_entries_for(character_id)` — 获取某角色可见的环境条目
- `update_entry(id, data)` — 更新条目（如修改可见角色列表）
- `remove_entry(id)` — 删除条目
- `all_entries()` — 获取全部条目（供判断机制全知视角）
- 支持检查点后清理过期条目

## Acceptance criteria

- [ ] DialogueLog 按时间顺序追加和读取
- [ ] 空 dialogue 不追加到日志
- [ ] EnvironmentStore 按 `visible_to` 正确过滤角色可见条目
- [ ] 更新/删除环境条目正常工作
- [ ] 单元测试覆盖两个模块的所有方法

## Blocked by

- #1 — 核心类型定义
