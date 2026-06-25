# Issue #10: 战役背景解析器

## What to build

实现战役背景的解析和管理模块。

- `parse_campaign_background(user_input)` — 解析用户输入的战役背景：
  - **短文本（< 200 字）**：调用 LLM 基于用户简短描述扩展出结构化世界观信息（势力、历史、地理、重要 NPC 等）
  - **长文本**：调用 LLM 从设定文档中提炼结构化世界观信息
  - 返回结构化的 CampaignBackground 对象
- `get_world_info()` — 运行时读取世界观信息，供环境动作单元、NPC 生成等模块查询
- `get_faction(name)` — 查询特定势力信息
- `get_history_period(timestamp)` — 查询特定历史时期信息
- 解析后的背景以结构化格式存储在企业内部，后续 Issue（ContextAssembler 扩展、环境生成）可以引用

## Acceptance criteria

- [ ] 短文本输入被 LLM 扩展为结构化背景
- [ ] 长文本输入被 LLM 提炼为结构化背景
- [ ] 返回的 CampaignBackground 包含世界观、势力、历史等结构化字段
- [ ] `get_world_info()` 和 `get_faction()` 可正常查询
- [ ] LLM 调用失败时有合理的降级处理（保留原始文本作为背景）
- [ ] 单元测试覆盖解析逻辑（mock LLM 响应）

## Blocked by

- #1 — 核心类型定义
- #7 — LLM Gateway（复用 LLM 调用层）
