# Issue #3: 角色存储 (CharacterStore)

## What to build

实现角色的档案和上下文的 CRUD 存储模块。

- 每个角色拥有两个独立数据结构：`CharacterProfile`（静态）和 `CharacterContext`（动作单元历史列表）
- 支持操作：
  - `create_character(profile)` — 创建角色（含档案初始化）
  - `get_profile(id)` / `update_profile(id, data)` — 档案读写
  - `append_context(id, ActionUnit)` — 追加动作单元到角色上下文
  - `get_context(id)` — 获取角色完整上下文
  - `get_all_characters()` — 获取所有角色列表
  - `create_npc_on_the_fly(name, description)` — 运行时即时创建 NPC（调用 LLM 生成角色档案，但此 Issue 中留桩，由后续 Issue 补上 LLM 调用）
- PC 和 NPC 共用同一存储结构，通过 `character_type` 字段区分

## Acceptance criteria

- [ ] 可创建角色并写入档案
- [ ] 可追加动作单元到角色上下文
- [ ] 可读取角色完整上下文（按时间排序）
- [ ] 可更新角色档案（如检查点更新性格描述）
- [ ] 支持即时创建 NPC（先以预设档案创建，LLM 调用留桩）
- [ ] 单元测试覆盖所有 CRUD 操作

## Blocked by

- #1 — 核心类型定义
