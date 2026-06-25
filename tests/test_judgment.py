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
                             sanity_check_interval=5, env_force_lambda=0.15)
        return eng, provider, st, cs

    def test_judge_normal(self, engine):
        eng, provider, st, cs = engine
        eng.env_force_lambda = 0.0  # 禁止泊松强制环境，纯靠 LLM 判断
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.add_characters(["npc_1"])
        st.process_action_unit(ActionUnit(character_id=None, action="初始环境", entered=["npc_1"]))
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
        # 用高 lambda 让 3 轮后几乎必命中强制环境
        eng.env_force_lambda = 10.0
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.add_characters(["npc_1"])
        st.process_action_unit(ActionUnit(character_id=None, action="初始环境", entered=["npc_1"]))
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

    def test_judge_no_force_when_count_low(self, engine):
        """count=0 时概率为 0，判定结果必为 LLM 返回值。"""
        eng, provider, st, cs = engine
        eng.env_force_lambda = 0.15
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.add_characters(["npc_1"])
        st.process_action_unit(ActionUnit(character_id=None, action="初始环境"))
        # 没有任何角色动作，count=0，p=0，绝不强制
        provider.set_responses([
            json.dumps({
                "next_speaker": "npc_1",
                "reason": "NPC继续",
                "force_environment": False,
                "corrected_present_characters": None,
            })
        ])
        result = eng.judge()
        assert result.next_speaker == "npc_1"
        assert result.force_environment is False

    def test_force_env_probability_monotonic(self, engine):
        """概率应随计数递增。"""
        eng, _, _, _ = engine
        eng.env_force_lambda = 0.15
        p0 = eng._force_env_probability(0)
        p3 = eng._force_env_probability(3)
        p5 = eng._force_env_probability(5)
        p10 = eng._force_env_probability(10)
        assert p0 == 0.0
        assert p3 < p5 < p10 < 1.0

    def test_judge_sanity_check_triggers(self, engine):
        eng, provider, st, cs = engine
        eng.env_force_lambda = 0.0
        cs.create_character(CharacterProfile(id="npc_1", name="NPC1"))
        st.add_characters(["npc_1"])
        st.process_action_unit(ActionUnit(character_id=None, action="初始环境", entered=["npc_1"]))
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
        st.add_characters(["npc_1"])
        st.process_action_unit(ActionUnit(character_id=None, action="初始环境", entered=["npc_1"]))
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
