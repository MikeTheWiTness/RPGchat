import random
import pytest
from rpg_chat.rules import SkillCheckHandler, D20_STANDARD


class TestSkillCheckHandler:
    @pytest.fixture
    def handler(self):
        h = SkillCheckHandler()
        h._dice._rng.seed(42)
        return h

    def test_not_a_check_directive_returns_none(self, handler):
        result = handler.handle_directive("随便说点啥", {}, {})
        assert result is None

    def test_empty_skill_name_returns_none(self, handler):
        result = handler.handle_directive("检定 ", {}, {})
        assert result is None

    def test_pure_narrative_mode_rejects(self, handler):
        result = handler.handle_directive("检定 说服", None, {"说服": 5})
        assert result.success is False
        assert "纯叙事" in result.result_description

    def test_check_with_explicit_dc(self, handler):
        handler._dice._rng = random.Random()
        handler._dice._rng.randint = lambda a, b: 12
        skills = {"说服": 3}
        result = handler.handle_directive("检定 说服 15", D20_STANDARD, skills)
        assert result.success is True
        assert result.skill_value == 3
        assert result.difficulty == 15
        assert "d20" in result.result_description
        assert "说服" in result.result_description

    def test_check_without_dc_uses_default_10(self, handler):
        handler._dice._rng = random.Random()
        handler._dice._rng.randint = lambda a, b: 8
        skills = {"说服": 3}
        result = handler.handle_directive("检定 说服", D20_STANDARD, skills)
        assert result.success is True
        assert result.difficulty == 10

    def test_unknown_skill_uses_zero_modifier(self, handler):
        handler._dice._rng = random.Random()
        handler._dice._rng.randint = lambda a, b: 10
        skills = {}
        result = handler.handle_directive("检定 不存在的技能 15", D20_STANDARD, skills)
        assert result.skill_value == 0

    def test_critical_hit_description(self, handler):
        handler._dice._rng = random.Random()
        handler._dice._rng.randint = lambda a, b: 20
        skills = {"攻击": 5}
        result = handler.handle_directive("检定 攻击 10", D20_STANDARD, skills)
        assert result.critical is True
        assert "暴击" in result.result_description

    def test_fumble_description(self, handler):
        handler._dice._rng = random.Random()
        handler._dice._rng.randint = lambda a, b: 1
        skills = {"攻击": 5}
        result = handler.handle_directive("检定 攻击 10", D20_STANDARD, skills)
        assert result.fumble is True
        assert "大失败" in result.result_description

    def test_description_contains_roll_and_dc(self, handler):
        handler._dice._rng = random.Random()
        handler._dice._rng.randint = lambda a, b: 14
        skills = {"运动": 2}
        result = handler.handle_directive("检定 运动 13", D20_STANDARD, skills)
        assert "d20=14" in result.result_description
        assert "DC13" in result.result_description
        assert "运动+2" in result.result_description

    def test_d20_standard_preset_exists(self):
        assert D20_STANDARD.system_name == "D20 Standard"
        assert D20_STANDARD.primary_dice == "d20"
        assert len(D20_STANDARD.attributes) > 0
        assert len(D20_STANDARD.skills) > 0
