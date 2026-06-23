import json
import re
from typing import Optional

from rpg_chat.types import ActionUnit, AgentDirective


class ParseError(Exception):
    pass


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
