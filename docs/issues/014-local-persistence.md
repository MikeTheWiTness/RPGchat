# Issue #14: 本地持久化服务

## What to build

实现游戏会话的本地文件保存和加载模块。

- `save(session, filepath?)` — 保存 GameSession 到本地 JSON 文件
  - 默认路径：`./saves/<session_name>.json`
  - 自动序列化所有数据结构（角色档案、上下文、环境条目、对话日志、检查点等）
  - 自动生成 backup 文件（`.json.bak`）
- `load(filepath)` — 从文件加载 GameSession
  - 验证文件完整性和 schema 兼容性
  - 尝试修复轻微的数据损坏
- `list_saves()` — 列出所有存档文件
- `delete_save(filepath)` — 删除存档
- 支持多种保存格式：JSON（可读、可调试）为主，后续可选二进制压缩

## Acceptance criteria

- [ ] 完整的 GameSession 保存后加载，数据一致
- [ ] 自动 backup 文件生成
- [ ] 存档文件列表可查看
- [ ] 存档可删除
- [ ] 损坏的存档文件被检测并提示
- [ ] 集成测试覆盖保存→加载→验证完整流程

## Blocked by

- #3 — CharacterStore
- #4 — DialogueLog + EnvironmentStore
- #5 — SceneTracker
