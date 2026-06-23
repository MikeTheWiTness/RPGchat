import pytest
from rpg_chat.rules import SkillCheckHandler, PRESETS, COC_7TH, DND_5E
from rpg_chat.types import RulesConfig


class TestSkillCheckHandler:
    @pytest.fixture
    def handler(self):
        return SkillCheckHandler()

    def test_coc_check_success_format(self, handler):
        result = handler.handle_directive(
            "检定 侦查", COC_7TH, {"侦查": 60}
        )
        assert result is not None
        assert "d100=" in result.result_description
        assert "侦查" in result.result_description
        assert result.skill_value == 60

    def test_dnd_check_format(self, handler):
        result = handler.handle_directive(
            "检定 运动", DND_5E, {"运动": 5}
        )
        assert result is not None
        assert "d20=" in result.result_description
        assert "运动" in result.result_description

    def test_not_a_check_directive(self, handler):
        result = handler.handle_directive(
            "继续", COC_7TH, {"侦查": 60}
        )
        assert result is None

    def test_empty_skill_name(self, handler):
        result = handler.handle_directive(
            "检定 ", COC_7TH, {"侦查": 60}
        )
        assert result is None

    def test_pure_narrative_mode_rejects(self, handler):
        result = handler.handle_directive(
            "检定 侦查", None, {"侦查": 60}
        )
        assert result is not None
        assert result.result_description == "纯叙事模式不支持检定"

    def test_unknown_skill(self, handler):
        result = handler.handle_directive(
            "检定 超能力", COC_7TH, {"侦查": 60}
        )
        assert result is not None
        assert result.skill_value == 1

    def test_presets_loaded(self):
        assert "coc" in PRESETS
        assert "dnd" in PRESETS
        assert PRESETS["coc"].system_name == "CoC 7th"
        assert PRESETS["dnd"].system_name == "D&D 5e"

    def test_coc_has_skills(self):
        assert "侦查" in COC_7TH.skills
        assert COC_7TH.skills["侦查"]["base"] == 25

    def test_dnd_has_skills(self):
        assert "运动" in DND_5E.skills
        assert DND_5E.skills["运动"]["attribute"] == "STR"
