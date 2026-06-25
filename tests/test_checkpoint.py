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

    def test_checkpoint_cleans_up_old_environment_entries(self, setup):
        cm, provider, cs, es = setup
        provider.set_responses(["摘要内容。"])
        for i in range(8):
            es.add_entry(f"旧条目{i}", ["pc_1"])
        cs.create_character(CharacterProfile(id="pc_1", name="A"))
        cp = cm.trigger_checkpoint(
            stage_label="test",
            current_context="内容",
            character_profiles={"pc_1": cs.get_profile("pc_1")},
        )
        remaining = es.all_entries()
        old_count = sum(1 for e in remaining if not e.description.startswith("[检查点摘要"))
        assert old_count <= 5
        assert any("摘要内容" in e.description for e in remaining)

    def test_checkpoint_refreshes_fortune_for_characters(self, setup):
        from rpg_chat.fortune import FortuneSystem, FortuneLevel
        cm, provider, cs, es = setup
        provider.set_responses(["摘要内容。"])
        cs.create_character(CharacterProfile(id="pc_1", name="A"))
        cs.create_character(CharacterProfile(id="npc_1", name="B"))
        cp = cm.trigger_checkpoint(
            stage_label="test",
            current_context="内容",
            character_profiles={
                "pc_1": cs.get_profile("pc_1"),
                "npc_1": cs.get_profile("npc_1"),
            },
        )
        for char_id in ["pc_1", "npc_1"]:
            assert "fortune" in cp.character_updates[char_id]
            fortune = cp.character_updates[char_id]["fortune"]
            assert fortune in [level.value for level in FortuneLevel]

    def test_clean_departed_contexts_clears_units_keeps_profile(self, setup):
        from rpg_chat.types import ActionUnit
        cm, provider, cs, es = setup
        provider.set_responses(["摘要"])
        cs.create_character(CharacterProfile(id="pc_1", name="A"))
        cs.create_character(CharacterProfile(id="npc_gone", name="Gone"))
        cs.append_context("npc_gone", ActionUnit(
            character_id="npc_gone", action="离场前的动作"
        ))
        cs.append_context("pc_1", ActionUnit(
            character_id="pc_1", action="PC的动作"
        ))
        cm.clean_departed_contexts(["npc_gone"])
        gone_ctx = cs.get_context("npc_gone")
        assert len(gone_ctx.action_units) == 0
        assert cs.get_profile("npc_gone") is not None
        pc_ctx = cs.get_context("pc_1")
        assert len(pc_ctx.action_units) == 1

    def test_checkpoint_writes_fortune_to_character_context(self, setup):
        cm, provider, cs, es = setup
        provider.set_responses(["摘要内容。"])
        cs.create_character(CharacterProfile(id="pc_1", name="A"))
        ctx_before = cs.get_context("pc_1")
        ctx_before.fortune = "great_ominous"
        cm.trigger_checkpoint(
            stage_label="test",
            current_context="内容",
            character_profiles={"pc_1": cs.get_profile("pc_1")},
        )
        ctx_after = cs.get_context("pc_1")
        assert ctx_after.fortune != "great_ominous"
        from rpg_chat.fortune import FortuneLevel
        assert ctx_after.fortune in [level.value for level in FortuneLevel]
