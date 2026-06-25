import json
import re
from typing import Optional

from rpg_chat.types import ActionUnit, AgentDirective


class ParseError(Exception):
    pass


# 叙述切分：识别多种引号对话、中文括号内心活动
# “ = ", ” = ", ＂ = ", ‘ = ', ’ = '
_DIALOGUE_PATTERN = re.compile(
    r'[“”＂]([^“”＂]*)[“”＂]'
    r'|‘([^’]*)’'
    r'|「([^」]*)」'
    r'|『([^』]*)』'
)
_INNER_PATTERN = re.compile(r'[（\(]([^）\)]*)[）\)]')


def _first_group(m: re.Match) -> str:
    """取正则匹配中第一个非空捕获组的内容。"""
    for g in m.groups():
        if g is not None:
            return g
    return ""


def split_narrative(
    narrative: str,
    character_id: str | None = None,
    audience: list[str] | None = None,
    entered: list[str] | None = None,
    left: list[str] | None = None,
) -> list[ActionUnit]:
    """把连贯叙述文本按引号/括号边界切成多个 ActionUnit，保持顺序。

    规则（最简版）：
    - \"...\" / ""..."" / "...' / 「...」 / 『...』 → dialogue
    - （...） / (...) → inner_thought
    - 标记之间的纯文本 → action（整段保留，不按句号再切）
    - 空段跳过
    - 所有段共享 character_id/audience/entered/left
    """
    if not narrative or not narrative.strip():
        return []

    # 合并所有标记及其类型，按出现位置排序
    tokens: list[tuple[int, int, str, str]] = []  # (start, end, kind, text)
    for m in _DIALOGUE_PATTERN.finditer(narrative):
        tokens.append((m.start(), m.end(), "dialogue", _first_group(m)))
    for m in _INNER_PATTERN.finditer(narrative):
        tokens.append((m.start(), m.end(), "inner", _first_group(m)))
    tokens.sort(key=lambda t: t[0])

    units: list[ActionUnit] = []
    cursor = 0
    for start, end, kind, text in tokens:
        # 标记前的纯文本 → action
        if start > cursor:
            between = narrative[cursor:start].strip()
            if between:
                units.append(ActionUnit(
                    character_id=character_id,
                    action=between,
                    audience=audience,
                    entered=entered if not units else None,
                    left=left if not units else None,
                ))
        if kind == "dialogue":
            units.append(ActionUnit(
                character_id=character_id,
                dialogue=text.strip(),
                audience=audience,
            ))
        else:  # inner
            units.append(ActionUnit(
                character_id=character_id,
                inner_thought=text.strip(),
                audience=audience,
            ))
        cursor = end

    # 末尾剩余纯文本 → action
    if cursor < len(narrative):
        tail = narrative[cursor:].strip()
        if tail:
            units.append(ActionUnit(
                character_id=character_id,
                action=tail,
                audience=audience,
                entered=entered if not units else None,
                left=left if not units else None,
            ))

    # 若完全没有标记，整段作为 action
    if not units:
        units.append(ActionUnit(
            character_id=character_id,
            action=narrative.strip(),
            audience=audience,
            entered=entered,
            left=left,
        ))

    # entered/left 只挂在第一段
    if units:
        units[0].entered = entered
        units[0].left = left

    return units


def parse_pc_input(text: str) -> tuple[Optional[ActionUnit], Optional[AgentDirective]]:
    if not text.strip():
        raise ParseError("输入不能为空")

    directive = None

    directive_match = re.search(r'\{([^}]*)\}$', text)
    if directive_match:
        directive = AgentDirective(content=directive_match.group(1))
        text = text[:directive_match.start()].strip()

    dialogues = re.findall(r'【([^】]*)】', text)
    dialogue = "\n".join(dialogues) if dialogues else None

    inner_thought = None
    thought_match = re.search(r'（([^）]*)）', text)
    if thought_match:
        inner_thought = thought_match.group(1)

    action_text = text
    action_text = re.sub(r'【[^】]*】', '', action_text)
    if thought_match:
        action_text = action_text.replace(thought_match.group(0), '').strip()

    action_text = re.sub(r'\s+', ' ', action_text).strip()
    action = action_text if action_text else None

    if not dialogue and not action and not inner_thought:
        if directive:
            return None, directive
        raise ParseError("对话、行动、内心活动至少有一项不为空")

    return ActionUnit(
        character_id=None,
        dialogue=dialogue,
        action=action,
        inner_thought=inner_thought,
    ), directive


def validate_action_unit_json(json_str: str) -> ActionUnit:
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ParseError(f"JSON 解析失败: {e}")

    # 优先使用 narrative 字段（新格式），拆成多段后只返回第一段标记
    # 调用方应使用 split_narrative 拿到完整列表
    narrative = data.get("narrative")
    if narrative:
        # 临时塞入 action 字段供调用方识别；实际拆分在 game_loop 完成
        au = ActionUnit(
            character_id=data.get("character_id"),
            dialogue=None,
            action=narrative,  # 暂存 narrative 到 action
            inner_thought=None,
            audience=data.get("audience"),
            entered=data.get("entered"),
            left=data.get("left"),
        )
        au._narrative = narrative  # type: ignore[attr-defined]
        return au

    au = ActionUnit(
        character_id=data.get("character_id"),
        dialogue=data.get("dialogue"),
        action=data.get("action"),
        inner_thought=data.get("inner_thought"),
        audience=data.get("audience"),
        entered=data.get("entered"),
        left=data.get("left"),
    )

    if not au.dialogue and not au.action and not au.inner_thought:
        raise ParseError("对话、行动、内心活动至少有一项不为空")

    return au
