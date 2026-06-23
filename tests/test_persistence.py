import json
import tempfile
import os
from pathlib import Path

import pytest
from rpg_chat.persistence import save, load, list_saves, delete_save
from rpg_chat.types import (
    ActionUnit,
    CharacterContext,
    CharacterProfile,
    DialogueEntry,
    EnvironmentEntry,
    GameSession,
    SceneState,
    CampaignBackground,
    RulesConfig,
)


class TestPersistence:
    @pytest.fixture
    def session(self):
        s = GameSession(
            id="test-session-1",
            name="测试团",
            mode="player-present",
            mechanics_mode="pure-narrative",
            characters={
                "pc_alice": CharacterProfile(
                    id="pc_alice",
                    name="Alice",
                    character_type="pc",
                    personality="勇敢",
                    skills={"剑术": 70},
                ),
                "npc_bob": CharacterProfile(
                    id="npc_bob",
                    name="Bob",
                    character_type="npc",
                    personality="狡猾",
                ),
            },
            character_contexts={
                "pc_alice": CharacterContext(
                    character_id="pc_alice",
                    action_units=[
                        ActionUnit(
                            character_id="pc_alice",
                            dialogue="你好",
                            action="挥手",
                        )
                    ],
                ),
                "npc_bob": CharacterContext(
                    character_id="npc_bob",
                    action_units=[
                        ActionUnit(
                            character_id="npc_bob",
                            dialogue="欢迎",
                            inner_thought="可疑的人",
                        )
                    ],
                ),
            },
            environment_entries=[
                EnvironmentEntry(
                    id="env-1",
                    description="昏暗的酒馆",
                    visible_to=["pc_alice", "npc_bob"],
                ),
                EnvironmentEntry(
                    id="env-2",
                    description="暗门后的密室",
                    visible_to=["npc_bob"],
                ),
            ],
            dialogue_log=[
                DialogueEntry(
                    character_id="pc_alice",
                    dialogue="你好",
                    timestamp="2025-01-01T00:00:00Z",
                )
            ],
            scene_state=SceneState(
                present_characters=["pc_alice", "npc_bob"],
                action_count_since_env=3,
                total_action_count=10,
            ),
            campaign_background=CampaignBackground(
                raw_input="一片奇幻大陆",
                world_setting="艾泽拉斯风格的世界",
            ),
            rules_config=RulesConfig(
                system_name="CoC 7th",
                primary_dice="d100",
            ),
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        return s

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    def test_save_and_load_roundtrip(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)

        assert Path(filepath).exists()

        loaded = load(filepath)
        assert loaded.id == "test-session-1"
        assert loaded.name == "测试团"
        assert loaded.mode == "player-present"

    def test_save_creates_backup(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        save(session, filepath)

        backup = filepath + ".bak"
        assert Path(backup).exists()

    def test_characters_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        assert "pc_alice" in loaded.characters
        assert loaded.characters["pc_alice"].name == "Alice"
        assert loaded.characters["pc_alice"].personality == "勇敢"
        assert loaded.characters["pc_alice"].skills["剑术"] == 70

    def test_character_contexts_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        alice_ctx = loaded.character_contexts["pc_alice"]
        assert len(alice_ctx.action_units) == 1
        assert alice_ctx.action_units[0].dialogue == "你好"
        assert alice_ctx.action_units[0].action == "挥手"

        bob_ctx = loaded.character_contexts["npc_bob"]
        assert bob_ctx.action_units[0].inner_thought == "可疑的人"

    def test_environment_entries_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        assert len(loaded.environment_entries) == 2
        assert loaded.environment_entries[0].description == "昏暗的酒馆"
        assert loaded.environment_entries[0].visible_to == ["pc_alice", "npc_bob"]

    def test_dialogue_log_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        assert len(loaded.dialogue_log) == 1
        assert loaded.dialogue_log[0].dialogue == "你好"

    def test_scene_state_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        assert loaded.scene_state.present_characters == ["pc_alice", "npc_bob"]
        assert loaded.scene_state.action_count_since_env == 3
        assert loaded.scene_state.total_action_count == 10

    def test_campaign_background_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        assert loaded.campaign_background.raw_input == "一片奇幻大陆"
        assert loaded.campaign_background.world_setting == "艾泽拉斯风格的世界"

    def test_rules_config_preserved(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        loaded = load(filepath)

        assert loaded.rules_config.system_name == "CoC 7th"
        assert loaded.rules_config.primary_dice == "d100"

    def test_save_auto_path(self, session, temp_dir):
        cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            save(session)
            saves_dir = Path(temp_dir) / "saves"
            assert saves_dir.exists()
            files = list(saves_dir.glob("*.json"))
            assert len(files) == 1
            assert files[0].name == "测试团.json"
        finally:
            os.chdir(cwd)

    def test_load_nonexistent_raises(self, temp_dir):
        filepath = os.path.join(temp_dir, "nonexistent.json")
        with pytest.raises(FileNotFoundError, match="不存在"):
            load(filepath)

    def test_load_corrupted_file_raises(self, temp_dir):
        filepath = os.path.join(temp_dir, "bad.json")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("not json")
        with pytest.raises(ValueError, match="已损坏"):
            load(filepath)

    def test_load_invalid_format_raises(self, temp_dir):
        filepath = os.path.join(temp_dir, "bad.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        with pytest.raises(ValueError, match="格式不正确"):
            load(filepath)

    def test_load_missing_fields_raises(self, temp_dir):
        filepath = os.path.join(temp_dir, "bad.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"foo": "bar"}, f)
        with pytest.raises(ValueError, match="缺少必要字段"):
            load(filepath)

    def test_list_saves(self, session, temp_dir):
        save_dir = os.path.join(temp_dir, "saves")
        os.makedirs(save_dir)
        save(session, os.path.join(save_dir, "a.json"))
        save(session, os.path.join(save_dir, "b.json"))
        saves = list_saves(save_dir)
        assert len(saves) == 2

    def test_list_saves_empty_dir(self, temp_dir):
        save_dir = os.path.join(temp_dir, "nonexistent")
        saves = list_saves(save_dir)
        assert saves == []

    def test_list_saves_excludes_backup(self, session, temp_dir):
        save_dir = os.path.join(temp_dir, "saves")
        os.makedirs(save_dir)
        save(session, os.path.join(save_dir, "x.json"))
        save(session, os.path.join(save_dir, "x.json"))
        saves = list_saves(save_dir)
        assert len(saves) == 1

    def test_delete_save(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        assert Path(filepath).exists()
        delete_save(filepath)
        assert not Path(filepath).exists()

    def test_delete_save_also_removes_backup(self, session, temp_dir):
        filepath = os.path.join(temp_dir, "test.json")
        save(session, filepath)
        save(session, filepath)
        assert Path(filepath + ".bak").exists()
        delete_save(filepath)
        assert not Path(filepath + ".bak").exists()

    def test_session_null_campaign_background(self, temp_dir):
        session = GameSession(
            id="s1",
            name="minimal",
            campaign_background=None,
            rules_config=None,
        )
        filepath = os.path.join(temp_dir, "min.json")
        save(session, filepath)
        loaded = load(filepath)
        assert loaded.campaign_background is None
        assert loaded.rules_config is None
