import json
import pytest
from rpg_chat.llm import MockLLMProvider, LLMGateway
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.judgment import JudgmentEngine
from rpg_chat.types import ActionUnit, CharacterProfile


class TestJudgmentEngine:
    @pytest.fixture
    def engine(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        eng = JudgmentEngine(gateway, ca, st, max_consecutive_characters=3,
                             sanity_check_interval=5)
        return eng, provider, st, cs

    def test_judge_normal(self, engine):
        eng, provider, st, cs = engine
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.process_action_unit(ActionUnit(character_id="env", entered=["npc_1"]))
        provider.set_responses([
            json.dumps({
                "next_speaker": "npc_1",
                "reason": "NPC该说话了",
                "force_environment": False,
                "corrected_present_characters": None,
            })
        ])
        result = eng.judge()
        assert result.next_speaker == "npc_1"
        assert result.force_environment is False

    def test_judge_force_environment(self, engine):
        eng, provider, st, cs = engine
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.process_action_unit(ActionUnit(character_id="env", entered=["npc_1"]))
        st.process_action_unit(ActionUnit(character_id="npc_1", dialogue="1"))
        st.process_action_unit(ActionUnit(character_id="npc_1", dialogue="2"))
        st.process_action_unit(ActionUnit(character_id="npc_1", dialogue="3"))

        provider.set_responses([
            json.dumps({
                "next_speaker": "npc_1",
                "reason": "本来应该NPC",
                "force_environment": False,
                "corrected_present_characters": None,
            })
        ])
        result = eng.judge()
        assert result.next_speaker == "environment"
        assert result.force_environment is True

    def test_judge_sanity_check_triggers(self, engine):
        eng, provider, st, cs = engine
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.process_action_unit(ActionUnit(character_id="env", entered=["npc_1"]))
        for _ in range(4):
            st.process_action_unit(ActionUnit(character_id="npc_1", dialogue="x"))

        provider.set_responses([
            json.dumps({
                "next_speaker": "npc_1",
                "reason": "继续",
                "force_environment": False,
                "corrected_present_characters": ["npc_1", "npc_new"],
            })
        ])
        result = eng.judge()
        assert result.corrected_present_characters == ["npc_1", "npc_new"]
        assert "npc_new" in st.get_present()

    def test_generate_environment(self, engine):
        eng, provider, st, cs = engine
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.process_action_unit(ActionUnit(character_id="env", entered=["npc_1"]))
        provider.set_responses([
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "浓雾笼罩了森林",
                "inner_thought": None,
            })
        ])
        au = eng.generate_environment()
        assert au.character_id is None
        assert au.action == "浓雾笼罩了森林"
