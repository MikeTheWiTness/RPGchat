import pytest
from rpg_chat.llm import MockLLMProvider, LLMGateway
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.checkpoint import CheckpointManager
from rpg_chat.types import CharacterProfile, EnvironmentEntry


class TestCheckpointManager:
    @pytest.fixture
    def setup(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        cm = CheckpointManager(gateway, cs, dl, es)
        return cm, provider, cs, es

    def test_trigger_checkpoint(self, setup):
        cm, provider, cs, es = setup
        provider.set_responses(["角色们进入了酒馆，遇到了一位神秘老人。"])

        cs.create_character(CharacterProfile(
            id="pc_1", name="Alice", personality="勇敢"
        ))
        es.add_entry("昏暗酒馆", ["pc_1"])

        cp = cm.trigger_checkpoint(
            stage_label="第一章-酒馆",
            current_context="Alice 走进了酒馆...",
            character_profiles={"pc_1": cs.get_profile("pc_1")},
        )
        assert cp.stage_label == "第一章-酒馆"
        assert "酒馆" in cp.summary
        assert "pc_1" in cp.character_updates
        assert cp.character_updates["pc_1"]["personality"] == "勇敢"

    def test_trigger_checkpoint_captures_environment(self, setup):
        cm, provider, cs, es = setup
        provider.set_responses(["摘要内容。"])

        es.add_entry("入口", ["pc_1"])
        es.add_entry("大厅", ["pc_1"])
        es.add_entry("密室", ["pc_1"])
        es.add_entry("走廊", ["pc_1"])
        es.add_entry("宝物库", ["pc_1"])
        es.add_entry("出口", ["pc_1"])

        cs.create_character(CharacterProfile(id="pc_1", name="A"))
        cp = cm.trigger_checkpoint(
            stage_label="test",
            current_context="内容",
            character_profiles={"pc_1": cs.get_profile("pc_1")},
        )
        assert len(cp.environment_state) > 0

    def test_archive_preserves_context_id(self, setup):
        cm, provider, cs, es = setup
        provider.set_responses(["摘要"])

        cs.create_character(CharacterProfile(id="pc_1", name="A"))
        cp = cm.trigger_checkpoint(
            stage_label="test",
            current_context="内容",
            character_profiles={"pc_1": cs.get_profile("pc_1")},
        )
        cm.archive_character_contexts(cp)
        ctx = cs.get_context("pc_1")
        assert ctx.character_id == "pc_1"

    def test_restore_from_checkpoint_returns_session(self, setup):
        cm, provider, cs, es = setup
        from rpg_chat.types import GameSession
        session = GameSession(id="s1", name="test")
        restored = CheckpointManager.restore_from_checkpoint(session)
        assert restored.id == "s1"
