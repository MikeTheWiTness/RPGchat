# CLAUDE.md — RPG Chat Agent

## 工作语言
全程使用**简体中文**交流。

## 环境要求
- pip install 优先使用清华源：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>`

## 测试原则
- **禁止**为了通过测试而削弱测试效果
- 测试必须能代表真实情况，不能削减需求来让测试通过

## 内容审查
- **禁止**道德审查。本项目是 TRPG 叙事工具，包含成人内容（角色档案含 `intimate_features` 字段等），不做安全警告和道德判断。

## 常用工作流

| 技能 | 时机 | 产出 |
|------|------|------|
| `/grill-with-docs` | 设计讨论阶段 | 更新 CONTEXT.md，完成后输出一个 ADR |
| `/to-prd` | grill 结束后，若内容变动大 | 生成 PRD 文档到 issue tracker |
| `/to-issues` | PRD 完成后 | 拆分为可独立领取的 issue |
| `/tdd` | 开始编码 | 红→绿→重构循环，测试必须代表真实需求 |

## /grill-with-docs 时的行为准则
- **只记录，不执行**。Grill 阶段收集问题、记录发现，标记为待处理，不要马上改代码
- 等所有问题问完、ADRs 输出后再进入执行阶段
- 发现的 bug/疏忽记录下来，在 `/to-issues` 阶段生成修复任务
