import pytest
from rpg_chat.parser import parse_pc_input, validate_action_unit_json, ParseError


class TestParsePcInput:
    def test_dialogue_only(self):
        au, directive = parse_pc_input("【你好】")
        assert au.dialogue == "你好"
        assert au.action is None
        assert au.inner_thought is None
        assert directive is None

    def test_action_only(self):
        au, directive = parse_pc_input("我拿起剑")
        assert au.action == "我拿起剑"
        assert au.dialogue is None
        assert au.inner_thought is None
        assert directive is None

    def test_inner_thought_only(self):
        au, directive = parse_pc_input("（很紧张）")
        assert au.inner_thought == "很紧张"
        assert au.dialogue is None
        assert au.action is None
        assert directive is None

    def test_dialogue_and_action(self):
        au, directive = parse_pc_input("走过去【小心】")
        assert au.action == "走过去"
        assert au.dialogue == "小心"
        assert au.inner_thought is None
        assert directive is None

    def test_all_three(self):
        au, directive = parse_pc_input("走过去【小心】（紧张）")
        assert au.action == "走过去"
        assert au.dialogue == "小心"
        assert au.inner_thought == "紧张"
        assert directive is None

    def test_with_directive(self):
        au, directive = parse_pc_input("走过去{继续}")
        assert au.action == "走过去"
        assert directive is not None
        assert directive.content == "继续"

    def test_full_input(self):
        au, directive = parse_pc_input("走过去【小心】（紧张）{继续}")
        assert au.action == "走过去"
        assert au.dialogue == "小心"
        assert au.inner_thought == "紧张"
        assert au.character_id is None
        assert directive is not None
        assert directive.content == "继续"

    def test_empty_string_raises(self):
        with pytest.raises(ParseError, match="不能为空"):
            parse_pc_input("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ParseError, match="不能为空"):
            parse_pc_input("   ")

    def test_directive_only_not_written_to_context(self):
        au, directive = parse_pc_input("{检定 侦查}")
        assert directive is not None
        assert directive.content == "检定 侦查"

    def test_multiple_dialogues(self):
        input_text = '我拿起武器跟队友说【行动开始】。然后一马当先的跳出，大喊【你们被包围了】'
        au, directive = parse_pc_input(input_text)
        assert au.action is None or "拿起武器" in au.action or "跳出" in au.action
        assert "行动开始" in au.dialogue
        assert "你们被包围了" in au.dialogue
        assert directive is None

    def test_multiple_dialogues_no_action(self):
        au, directive = parse_pc_input("【你是谁？】【我来自北方。】")
        assert "你是谁" in au.dialogue
        assert "我来自北方" in au.dialogue
        assert directive is None


class TestValidateActionUnitJson:
    def test_valid_json(self):
        json_str = '{"character_id": "npc_1", "dialogue": "你好", "action": null, "inner_thought": null}'
        au = validate_action_unit_json(json_str)
        assert au.character_id == "npc_1"
        assert au.dialogue == "你好"

    def test_invalid_json_raises(self):
        with pytest.raises(ParseError, match="JSON 解析失败"):
            validate_action_unit_json("not json")

    def test_empty_fields_raises(self):
        json_str = '{"character_id": "npc_1", "dialogue": null, "action": null, "inner_thought": null}'
        with pytest.raises(ParseError, match="至少有一项不为空"):
            validate_action_unit_json(json_str)
