import json
import pytest
from rpg_chat.llm import MockLLMProvider, LLMGateway
from rpg_chat.campaign import CampaignBackgroundParser
from rpg_chat.types import CampaignBackground


class TestCampaignBackgroundParser:
    @pytest.fixture
    def parser(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        return CampaignBackgroundParser(gateway), provider

    def test_parse_short_text(self, parser):
        p, provider = parser
        provider.set_responses([
            json.dumps({
                "world_setting": "扩展后的世界",
                "factions": [{"name": "王国", "description": "一个王国"}],
                "history": [{"period": "远古", "events": "龙之战"}],
                "important_locations": [{"name": "铁炉堡", "description": "矮人城"}],
                "initial_situation": "冒险者集合",
            })
        ])
        result = p.parse("一个奇幻世界")
        assert result.world_setting == "扩展后的世界"
        assert result.raw_input == "一个奇幻世界"
        assert len(result.factions) == 1
        assert len(result.history) == 1
        assert len(result.important_locations) == 1
        assert result.initial_situation == "冒险者集合"

    def test_parse_long_text(self, parser):
        p, provider = parser
        long_text = "A" * 250
        provider.set_responses([
            json.dumps({
                "world_setting": "提炼后的世界",
                "factions": [],
                "history": [],
                "important_locations": [],
                "initial_situation": "",
            })
        ])
        result = p.parse(long_text)
        assert result.world_setting == "提炼后的世界"

    def test_get_world_info(self, parser):
        p, provider = parser
        bg = CampaignBackground(
            raw_input="测试",
            world_setting="一个魔法世界",
        )
        assert p.get_world_info(bg) == "一个魔法世界"

    def test_get_faction_found(self, parser):
        p, provider = parser
        bg = CampaignBackground(
            raw_input="测试",
            factions=[
                {"name": "北方王国", "description": "强大的王国"},
                {"name": "暗影公会", "description": "秘密组织"},
            ],
        )
        faction = p.get_faction(bg, "北方王国")
        assert faction is not None
        assert faction["description"] == "强大的王国"

    def test_get_faction_not_found(self, parser):
        p, provider = parser
        bg = CampaignBackground(raw_input="测试", factions=[])
        assert p.get_faction(bg, "不存在") is None

    def test_get_history_period(self, parser):
        p, provider = parser
        bg = CampaignBackground(
            raw_input="测试",
            history=[
                {"period": "黄金时代", "events": "繁荣昌盛"},
                {"period": "黑暗时代", "events": "战乱不断"},
            ],
        )
        result = p.get_history_period(bg, "黑暗时代")
        assert result is not None
        assert result["events"] == "战乱不断"
