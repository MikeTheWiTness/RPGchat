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

    def test_assemble_for_character_includes_fortune(self, stores, assembler):
        cs, dl, es, st = stores
        cs.create_character(CharacterProfile(id="npc_1", name="Bob"))
        ctx = cs.get_context("npc_1")
        ctx.fortune = "auspicious"

        result = assembler.assemble_for_character("npc_1")
        assert result["fortune"] == "auspicious"


class TestAudienceVisibility:
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

    def test_restricted_audience_only_visible_to_target(self, stores, assembler):
        """audience 限制的动作单元仅对指定角色可见"""
        cs, dl, es, st = stores
        cs.create_character(CharacterProfile(id="npc_bob", name="Bob"))
        cs.create_character(CharacterProfile(id="npc_charlie", name="Charlie"))

        # Bob 说悄悄话，只有 Charlie 能听到
        whisper = ActionUnit(
            character_id="npc_bob",
            dialogue="Charlie，过来一下",
            audience=["npc_charlie"],
        )
        cs.append_context("npc_bob", whisper)

        # Charlie 公开回应
        public_reply = ActionUnit(
            character_id="npc_charlie",
            dialogue="什么事？",
        )
        cs.append_context("npc_charlie", public_reply)

        st.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_bob", "npc_charlie"])
        )

        # Charlie 能感知到 Bob 的悄悄话和自己的回应
        charlie_ctx = assembler.assemble_for_character("npc_charlie")
        perceived = charlie_ctx["perceived_actions"]
        perceived_dialogues = [au.dialogue for au in perceived]
        assert "Charlie，过来一下" in perceived_dialogues
        assert "什么事？" in perceived_dialogues

        # Bob 能感知到自己的悄悄话和 Charlie 的公开回应
        bob_ctx = assembler.assemble_for_character("npc_bob")
        perceived = bob_ctx["perceived_actions"]
        perceived_dialogues = [au.dialogue for au in perceived]
        assert "Charlie，过来一下" in perceived_dialogues
        assert "什么事？" in perceived_dialogues

    def test_public_audience_visible_to_all(self, stores, assembler):
        """audience=None 的动作单元对所有角色可见"""
        cs, dl, es, st = stores
        cs.create_character(CharacterProfile(id="npc_bob", name="Bob"))
        cs.create_character(CharacterProfile(id="npc_charlie", name="Charlie"))
        cs.create_character(CharacterProfile(id="npc_diana", name="Diana"))

        public_action = ActionUnit(
            character_id="npc_bob",
            dialogue="大家听我说",
        )
        cs.append_context("npc_bob", public_action)

        st.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_bob", "npc_charlie", "npc_diana"])
        )

        for cid in ["npc_bob", "npc_charlie", "npc_diana"]:
            ctx = assembler.assemble_for_character(cid)
            perceived_dialogues = [au.dialogue for au in ctx["perceived_actions"]]
            assert "大家听我说" in perceived_dialogues, f"{cid} 应该能看到公开动作"

    def test_excluded_character_cannot_see_restricted_action(self, stores, assembler):
        """不在 audience 中的角色看不到受限动作单元"""
        cs, dl, es, st = stores
        cs.create_character(CharacterProfile(id="npc_bob", name="Bob"))
        cs.create_character(CharacterProfile(id="npc_charlie", name="Charlie"))
        cs.create_character(CharacterProfile(id="npc_diana", name="Diana"))

        secret = ActionUnit(
            character_id="npc_bob",
            dialogue="Charlie，过来一下",
            inner_thought="Diana 不能知道这个",
            audience=["npc_charlie"],
        )
        cs.append_context("npc_bob", secret)

        st.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_bob", "npc_charlie", "npc_diana"])
        )

        diana_ctx = assembler.assemble_for_character("npc_diana")
        perceived = diana_ctx["perceived_actions"]
        perceived_dialogues = [au.dialogue for au in perceived]
        perceived_thoughts = [au.inner_thought for au in perceived]
        assert "Charlie，过来一下" not in perceived_dialogues
        assert "Diana 不能知道这个" not in perceived_thoughts
