import pytest
from rpg_chat.preset_loader import (
    load_character,
    list_characters,
    load_world,
    list_worlds,
)
from rpg_chat.types import CharacterProfile, CampaignBackground


class TestPresetCharacterLoader:
    def test_list_characters_returns_list(self):
        chars = list_characters()
        assert isinstance(chars, list)
        assert "酒馆老板加雷斯" in chars

    def test_load_character_by_name(self):
        profile = load_character("酒馆老板加雷斯")
        assert profile is not None
        assert isinstance(profile, CharacterProfile)
        assert profile.name == "加雷斯·铁壶"
        assert profile.character_type == "npc"
        assert len(profile.skills) >= 3
        assert len(profile.personality) > 50

    def test_load_character_by_name_without_extension(self):
        profile = load_character("酒馆老板加雷斯.json")
        assert profile is not None
        assert profile.name == "加雷斯·铁壶"

    def test_load_character_not_found(self):
        profile = load_character("不存在的角色")
        assert profile is None

    def test_load_character_has_all_fields(self):
        profile = load_character("神秘旅者艾拉")
        assert profile.id == "mysterious_stranger_elara"
        assert len(profile.background) > 100
        assert len(profile.appearance) > 50
        assert len(profile.relationships) >= 2
        assert len(profile.notes) > 20

    def test_load_character_knight(self):
        profile = load_character("年轻骑士塞德里克")
        assert profile.name == "塞德里克·光盾"
        assert "剑术" in profile.skills
        assert profile.attributes.get("力量", 0) > 10

    def test_all_characters_loadable(self):
        for name in list_characters():
            profile = load_character(name)
            assert profile is not None, f"Failed to load: {name}"
            assert profile.name

    def test_realistic_character_has_physique(self):
        profile = load_character("前刑警佐佐木健吾")
        assert profile.physique.get("height") == "175cm"
        assert "weight" in profile.physique
        assert "build" in profile.physique

    def test_realistic_character_has_identity(self):
        profile = load_character("情报贩子井上真由子")
        assert profile.identity.get("occupation") is not None
        assert profile.identity.get("social_status") is not None

    def test_realistic_character_has_clothing(self):
        profile = load_character("极道千金黑川美雪")
        assert len(profile.clothing) > 50

    def test_realistic_character_has_behavior(self):
        profile = load_character("前刑警佐佐木健吾")
        assert "habits" in profile.behavior
        assert "quirks" in profile.behavior
        assert "mannerisms" in profile.behavior

    def test_realistic_character_has_intimate_features(self):
        profile = load_character("情报贩子井上真由子")
        assert len(profile.intimate_features) > 20

    def test_fantasy_character_has_extended_fields(self):
        profile = load_character("神秘旅者艾拉")
        assert isinstance(profile.physique, dict)
        assert isinstance(profile.identity, dict)
        assert isinstance(profile.behavior, dict)
        assert len(profile.intimate_features) > 10


class TestPresetWorldLoader:
    def test_list_worlds(self):
        worlds = list_worlds()
        assert isinstance(worlds, list)
        assert "艾瑟兰大陆" in worlds

    def test_load_world(self):
        bg = load_world("艾瑟兰大陆")
        assert bg is not None
        assert isinstance(bg, CampaignBackground)
        assert len(bg.world_setting) > 200
        assert len(bg.factions) == 7
        assert len(bg.history) >= 5
        assert len(bg.important_locations) == 7
        assert len(bg.initial_situation) > 100

    def test_load_world_factions_have_names(self):
        bg = load_world("艾瑟兰大陆")
        names = [f.get("name", "") for f in bg.factions]
        assert "北方联合王国" in names
        assert "南方神圣索拉帝国" in names

    def test_load_world_history_has_periods(self):
        bg = load_world("艾瑟兰大陆")
        periods = [h.get("period", "") for h in bg.history]
        combined = " ".join(periods)
        assert "诸神时代" in combined
        assert "魔晶战争" in combined

    def test_load_world_fantasy_has_power_system(self):
        bg = load_world("艾瑟兰大陆")
        assert len(bg.power_system) > 500
        assert "源流" in bg.power_system
        assert "魔法" in bg.power_system

    def test_load_realistic_world(self):
        bg = load_world("新东京暗流")
        assert bg is not None
        assert len(bg.factions) == 5
        assert len(bg.history) == 5
        assert len(bg.important_locations) == 5

    def test_load_realistic_world_power_system(self):
        bg = load_world("新东京暗流")
        assert len(bg.power_system) > 500
        assert "政治权力" in bg.power_system
        assert "经济资本" in bg.power_system
        assert "信息与情报" in bg.power_system

    def test_all_worlds_loadable(self):
        for name in list_worlds():
            bg = load_world(name)
            assert bg is not None, f"Failed to load world: {name}"
            assert bg.world_setting

    def test_load_world_not_found(self):
        bg = load_world("不存在的世界")
        assert bg is None


class TestPresetPathLoading:
    def test_load_character_by_absolute_path(self):
        from pathlib import Path
        import os
        presets_dir = Path(__file__).parent.parent / "presets" / "characters"
        path = presets_dir / "酒馆老板加雷斯.json"
        profile = load_character(str(path))
        assert profile is not None
        assert profile.name == "加雷斯·铁壶"

    def test_load_world_by_absolute_path(self):
        from pathlib import Path
        presets_dir = Path(__file__).parent.parent / "presets" / "worlds"
        path = presets_dir / "艾瑟兰大陆.json"
        bg = load_world(str(path))
        assert bg is not None
        assert len(bg.factions) == 7
