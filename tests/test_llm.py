import json
import pytest
from rpg_chat.llm import LLMGateway, MockLLMProvider, ParseError
from rpg_chat.types import CharacterProfile, ActionUnit


class TestLLMGateway:
    @pytest.fixture
    def mock_provider(self):
        return MockLLMProvider()

    @pytest.fixture
    def gateway(self, mock_provider):
        return LLMGateway(mock_provider)

    @pytest.fixture
    def npc_context(self):
        return {
            "profile": CharacterProfile(
                id="npc_bob", name="Bob", personality="暴躁的矮人铁匠"
            ),
            "own_action_units": [
                ActionUnit(
                    character_id="npc_bob",
                    dialogue="谁在敲门",
                    inner_thought="好烦",
                )
            ],
            "public_dialogue_history": [],
            "visible_environment": [],
            "present_characters": ["npc_bob", "pc_alice"],
        }

    def test_generate_npc_action_unit_success(self, mock_provider, npc_context):
        mock_provider.set_responses([
            json.dumps({
                "character_id": "npc_bob",
                "dialogue": "进来吧",
                "action": "打开门",
                "inner_thought": "最好别是推销的",
            })
        ])
        gateway = LLMGateway(mock_provider)
        au = gateway.generate_npc_action_unit(npc_context)
        assert au.character_id == "npc_bob"
        assert au.dialogue == "进来吧"
        assert au.action == "打开门"
        assert au.inner_thought == "最好别是推销的"

    def test_generate_npc_retries_on_bad_json(self, mock_provider, npc_context):
        mock_provider.set_responses([
            "not json",
            json.dumps({
                "character_id": "npc_bob",
                "dialogue": "重试成功",
            }),
        ])
        gateway = LLMGateway(mock_provider)
        au = gateway.generate_npc_action_unit(npc_context)
        assert au.dialogue == "重试成功"
        assert len(mock_provider.calls) == 2

    def test_generate_npc_fails_after_max_retries(self, mock_provider, npc_context):
        mock_provider.set_responses(["bad1", "bad2", "bad3"])
        gateway = LLMGateway(mock_provider)
        with pytest.raises(ParseError, match="已重试 2 次"):
            gateway.generate_npc_action_unit(npc_context)
        assert len(mock_provider.calls) == 3

    def test_generate_npc_retries_on_empty_json(self, mock_provider, npc_context):
        mock_provider.set_responses([
            json.dumps({"character_id": "npc_bob", "dialogue": None, "action": None, "inner_thought": None}),
            json.dumps({"character_id": "npc_bob", "dialogue": "好了"}),
        ])
        gateway = LLMGateway(mock_provider)
        au = gateway.generate_npc_action_unit(npc_context)
        assert au.dialogue == "好了"

    def test_npc_prompt_includes_fortune_description(self, mock_provider):
        from rpg_chat.fortune import FortuneSystem, FortuneLevel
        ctx = {
            "profile": CharacterProfile(
                id="npc_bob", name="Bob", personality="暴躁"
            ),
            "own_action_units": [],
            "public_dialogue_history": [],
            "visible_environment": [],
            "present_characters": ["npc_bob"],
            "fortune": "great_ominous",
        }
        mock_provider.set_responses([
            json.dumps({"character_id": "npc_bob", "dialogue": "倒霉"})
        ])
        gateway = LLMGateway(mock_provider)
        gateway.generate_npc_action_unit(ctx)
        system_prompt = mock_provider.system_calls[0]
        assert "大凶" in system_prompt

    def test_npc_prompt_includes_normal_fortune_by_default(self, mock_provider):
        ctx = {
            "profile": CharacterProfile(
                id="npc_bob", name="Bob", personality="暴躁"
            ),
            "own_action_units": [],
            "public_dialogue_history": [],
            "visible_environment": [],
            "present_characters": ["npc_bob"],
        }
        mock_provider.set_responses([
            json.dumps({"character_id": "npc_bob", "dialogue": "你好"})
        ])
        gateway = LLMGateway(mock_provider)
        gateway.generate_npc_action_unit(ctx)
        system_prompt = mock_provider.system_calls[0]
        assert "运势" in system_prompt

    def test_create_npc_profile_basic(self, mock_provider):
        mock_provider.set_responses([
            json.dumps({
                "id": "npc_goblin_01",
                "name": "Goblin",
                "personality": "胆小但狡猾",
                "background": "一只流浪的地精",
                "appearance": "绿色皮肤，尖耳朵",
                "skills": {"潜行": 60},
                "relationships": {},
                "notes": "",
            })
        ])
        gateway = LLMGateway(mock_provider)
        profile = gateway.create_npc_profile("Goblin", "一只小怪物")
        assert profile.name == "Goblin"
        assert profile.personality == "胆小但狡猾"
        assert profile.background == "一只流浪的地精"
        assert profile.character_type == "npc"

    def test_create_npc_profile_fallback_on_bad_json(self, mock_provider):
        mock_provider.set_responses(["not json"])
        gateway = LLMGateway(mock_provider)
        profile = gateway.create_npc_profile("Orc", "绿皮兽人")
        assert profile.name == "Orc"
        assert profile.personality == "绿皮兽人"
        assert profile.character_type == "npc"

    def test_generate_environment_action_unit(
        self, mock_provider
    ):
        mock_provider.set_responses([
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "天色渐暗，风声呼啸",
                "inner_thought": None,
            })
        ])
        gateway = LLMGateway(mock_provider)
        ctx = {
            "all_environment": [],
            "present_characters": ["pc_alice", "npc_bob"],
            "public_dialogue_history": [],
        }
        au = gateway.generate_environment_action_unit(ctx)
        assert au.character_id is None
        assert au.action == "天色渐暗，风声呼啸"

    def test_generate_judgment_normal(self, mock_provider):
        mock_provider.set_responses([
            json.dumps({
                "next_speaker": "npc_bob",
                "reason": "Bob 应该回应",
                "force_environment": False,
                "corrected_present_characters": None,
            })
        ])
        gateway = LLMGateway(mock_provider)
        ctx = {
            "present_characters": ["pc_alice", "npc_bob"],
            "public_dialogue_history": [],
        }
        result = gateway.generate_judgment(ctx)
        assert result["next_speaker"] == "npc_bob"
        assert result["force_environment"] is False
        assert result["corrected_present_characters"] is None

    def test_generate_judgment_with_sanity_check(self, mock_provider):
        mock_provider.set_responses([
            json.dumps({
                "next_speaker": "npc_bob",
                "reason": "继续",
                "force_environment": False,
                "corrected_present_characters": ["pc_alice", "npc_bob", "npc_new"],
            })
        ])
        gateway = LLMGateway(mock_provider)
        ctx = {
            "present_characters": ["pc_alice", "npc_bob"],
            "public_dialogue_history": [],
        }
        result = gateway.generate_judgment(ctx, sanity_check=True)
        assert result["corrected_present_characters"] == ["pc_alice", "npc_bob", "npc_new"]

    def test_generate_judgment_fallback_on_bad_json(self, mock_provider):
        mock_provider.set_responses(["not json"])
        gateway = LLMGateway(mock_provider)
        ctx = {"present_characters": [], "public_dialogue_history": []}
        result = gateway.generate_judgment(ctx)
        assert result["next_speaker"] == "environment"

    def test_generate_summary(self, mock_provider):
        mock_provider.set_responses(["角色们进入了地下城，遭遇了三只哥布林。"])
        gateway = LLMGateway(mock_provider)
        summary = gateway.generate_summary("长文本...")
        assert "哥布林" in summary

    def test_expand_campaign_background(self, mock_provider):
        mock_provider.set_responses([
            json.dumps({
                "world_setting": "一个中世纪奇幻世界",
                "factions": [{"name": "王国", "description": "北方王国"}],
                "history": [],
                "important_locations": [{"name": "铁炉堡", "description": "矮人城市"}],
                "initial_situation": "冒险者们在酒馆相遇",
            })
        ])
        gateway = LLMGateway(mock_provider)
        result = gateway.expand_campaign_background("中世纪奇幻")
        assert result["world_setting"] == "一个中世纪奇幻世界"
        assert len(result["factions"]) == 1

    def test_expand_campaign_background_fallback(self, mock_provider):
        mock_provider.set_responses(["not json"])
        gateway = LLMGateway(mock_provider)
        result = gateway.expand_campaign_background("中世纪奇幻")
        assert result["world_setting"] == "中世纪奇幻"
        assert result["factions"] == []

    def test_extract_campaign_background(self, mock_provider):
        mock_provider.set_responses([
            json.dumps({
                "world_setting": "末日废土",
                "factions": [],
                "history": [],
                "important_locations": [],
                "initial_situation": "",
            })
        ])
        gateway = LLMGateway(mock_provider)
        result = gateway.extract_campaign_background("在废土之上...")
        assert result["world_setting"] == "末日废土"


class TestCheckJudgment:
    @pytest.fixture
    def gateway(self):
        return LLMGateway(MockLLMProvider())

    def test_judge_check_needed(self, gateway):
        gateway._provider.set_responses([
            json.dumps({
                "needed": True,
                "skill": "说服",
                "dc": 15,
                "reason": "守卫警觉度高",
            })
        ])
        result = gateway.judge_check({
            "pc_action": "我说服守卫放行",
            "pc_profile": CharacterProfile(id="pc", name="PC"),
            "present_characters": ["pc", "guard"],
        })
        assert result["needed"] is True
        assert result["skill"] == "说服"
        assert result["dc"] == 15

    def test_judge_check_not_needed(self, gateway):
        gateway._provider.set_responses([
            json.dumps({
                "needed": False,
                "skill": "",
                "dc": 0,
                "reason": "普通对话无需检定",
            })
        ])
        result = gateway.judge_check({
            "pc_action": "我和店主打招呼",
            "pc_profile": CharacterProfile(id="pc", name="PC"),
            "present_characters": ["pc", "shopkeeper"],
        })
        assert result["needed"] is False

    def test_judge_check_fallback_on_bad_json(self, gateway):
        gateway._provider.set_responses(["not json"])
        result = gateway.judge_check({
            "pc_action": "我攻击哥布林",
            "pc_profile": CharacterProfile(id="pc", name="PC"),
            "present_characters": ["pc", "goblin"],
        })
        assert result["needed"] is False


class TestGeneratePCActionWithCheck:
    @pytest.fixture
    def gateway(self):
        return LLMGateway(MockLLMProvider())

    def test_generate_pc_action_with_success(self, gateway):
        gateway._provider.set_responses([
            json.dumps({
                "character_id": "pc",
                "dialogue": "守卫大人，行个方便",
                "action": "递上一袋金币，守卫犹豫后让开了路",
                "inner_thought": "幸好准备充分",
            })
        ])
        from rpg_chat.types import CheckResult, DiceRollResult
        check = CheckResult(
            success=True, critical=False, fumble=False,
            roll=DiceRollResult(expression="1d20+3", rolls=[14], modifier=3, total=17),
            skill_value=3, difficulty=15,
            result_description="d20=14 vs DC15 说服+3 → 成功",
        )
        au = gateway.generate_pc_action_with_check(
            {"pc_action": "我说服守卫放行"},
            check,
        )
        assert au.character_id == "pc"
        assert au.dialogue == "守卫大人，行个方便"
        assert "让开了路" in au.action

    def test_generate_pc_action_with_failure(self, gateway):
        gateway._provider.set_responses([
            json.dumps({
                "character_id": "pc",
                "dialogue": "守卫大人，行个方便",
                "action": "守卫冷笑一声，挥手拒绝",
                "inner_thought": "糟了，他不吃这套",
            })
        ])
        from rpg_chat.types import CheckResult, DiceRollResult
        check = CheckResult(
            success=False, critical=False, fumble=False,
            roll=DiceRollResult(expression="1d20+3", rolls=[5], modifier=3, total=8),
            skill_value=3, difficulty=15,
            result_description="d20=5 vs DC15 说服+3 → 失败",
        )
        au = gateway.generate_pc_action_with_check(
            {"pc_action": "我说服守卫放行"},
            check,
        )
        assert "拒绝" in au.action
        assert "糟了" in au.inner_thought
