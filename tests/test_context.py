import pytest
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.types import CharacterProfile, ActionUnit


class TestContextAssembler:
    @pytest.fixture
    def stores(self):
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        return cs, dl, es, st

    @pytest.fixture
    def assembler(self, stores):
        cs, dl, es, st = stores
        return ContextAssembler(cs, dl, es, st)

    def test_assemble_for_character_includes_own_context(self, stores, assembler):
        cs, dl, es, st = stores
        cs.create_character(
            CharacterProfile(id="npc_1", name="Bob", personality="暴躁")
        )
        cs.append_context(
            "npc_1",
            ActionUnit(
                character_id="npc_1",
                dialogue="你们好",
                inner_thought="我不喜欢这些人",
            ),
        )
        st.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_1"])
        )

        result = assembler.assemble_for_character("npc_1")
        assert result["profile"].name == "Bob"
        assert len(result["own_action_units"]) == 1
        assert result["own_action_units"][0].inner_thought == "我不喜欢这些人"

    def test_assemble_for_character_excludes_other_inner_thoughts(
        self, stores, assembler
    ):
        cs, dl, es, st = stores
        cs.create_character(
            CharacterProfile(id="npc_alice", name="Alice")
        )
        cs.create_character(
            CharacterProfile(id="npc_bob", name="Bob")
        )
        cs.append_context(
            "npc_alice", ActionUnit(character_id="npc_alice", dialogue="你好")
        )
        cs.append_context(
            "npc_bob",
            ActionUnit(
                character_id="npc_bob", dialogue="你好", inner_thought="紧张"
            ),
        )
        dl.append("npc_alice", "你好")
        dl.append("npc_bob", "你好")
        st.process_action_unit(
            ActionUnit(
                character_id="env", entered=["npc_alice", "npc_bob"]
            )
        )

        result = assembler.assemble_for_character("npc_alice")
        own_units = result["own_action_units"]
        for au in own_units:
            assert au.character_id == "npc_alice"

    def test_assemble_for_character_includes_visible_env(self, stores, assembler):
        cs, dl, es, st = stores
        cs.create_character(
            CharacterProfile(id="npc_1", name="Bob")
        )
        es.add_entry("公开线索", ["npc_1", "npc_2"])
        es.add_entry("秘密线索", ["npc_2"])
        st.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_1"])
        )

        result = assembler.assemble_for_character("npc_1")
        visible = result["visible_environment"]
        assert len(visible) == 1
        assert visible[0].description == "公开线索"

    def test_assemble_for_judgment_includes_all_profiles(self, stores, assembler):
        cs, dl, es, st = stores
        cs.create_character(CharacterProfile(id="npc_a", name="A"))
        cs.create_character(CharacterProfile(id="npc_b", name="B"))
        cs.append_context(
            "npc_a",
            ActionUnit(
                character_id="npc_a", inner_thought="秘密想法"
            ),
        )

        result = assembler.assemble_for_judgment()
        assert len(result["all_profiles"]) == 2
        assert result["all_contexts"]["npc_a"].action_units[0].inner_thought == "秘密想法"

    def test_assemble_for_judgment_includes_all_env(self, stores, assembler):
        cs, dl, es, st = stores
        es.add_entry("A", ["npc_1"])
        es.add_entry("B", ["npc_2"])
        es.add_entry("C", ["npc_3"])

        result = assembler.assemble_for_judgment()
        assert len(result["all_environment"]) == 3

    def test_assemble_includes_present_characters(self, stores, assembler):
        cs, dl, es, st = stores
        cs.create_character(CharacterProfile(id="npc_1", name="Bob"))
        st.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_1", "pc"])
        )

        result = assembler.assemble_for_character("npc_1")
        assert "pc" in result["present_characters"]

        result_j = assembler.assemble_for_judgment()
        assert "npc_1" in result_j["present_characters"]
