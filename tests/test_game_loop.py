import json
import pytest
from rpg_chat.llm import MockLLMProvider, LLMGateway
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.game_loop import GameLoop, GameLoopConfig
from rpg_chat.types import CharacterProfile


class TestGameLoop:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def test_new_game_creates_session(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "一个奇幻世界",
                "factions": [],
                "history": [],
                "important_locations": [],
                "initial_situation": "冒险者们在酒馆",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "阳光透过酒馆的窗户洒进来",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "由PC开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
            personality="勇敢的冒险者",
        )
        output = gl.new_game(
            name="测试团",
            campaign_input="一个奇幻世界",
            pc_profile=pc,
        )
        assert gl.session is not None
        assert gl.session.name == "测试团"
        assert "pc_alice" in gl.session.characters
        assert gl.session.campaign_background.world_setting == "一个奇幻世界"
        assert "阳光" in output
        assert "Alice" in output

    def test_new_game_initializes_scene(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境",
                "inner_thought": None,
                "entered": ["pc_alice", "npc_1"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        present = gl.present_characters
        assert "pc_alice" in present
        assert "npc_1" in present

    def test_handle_continue_npc(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({"world_setting": "世界", "factions": [], "history": [],
                        "important_locations": [], "initial_situation": ""}),
            json.dumps({"character_id": None, "dialogue": None, "action": "初始",
                        "inner_thought": None, "entered": ["pc_alice", "npc_bob"]}),
            json.dumps({"id": "npc_bob", "name": "Bob", "character_type": "npc",
                        "personality": "热情"}),
            json.dumps({"next_speaker": "npc_bob", "reason": "让NPC说话",
                        "force_environment": False, "corrected_present_characters": None}),
            json.dumps({"character_id": "npc_bob", "dialogue": "欢迎来到酒馆",
                        "action": "挥手", "inner_thought": "新来的冒险者"}),
            json.dumps({"character_id": "npc_bob", "dialogue": None,
                        "action": "他笑着挥了挥手，掌心的老茧在烛光下清晰可见。",
                        "inner_thought": None}),
            json.dumps({"next_speaker": "pc_alice", "reason": "轮到PC",
                        "force_environment": False, "corrected_present_characters": None}),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{继续}")
        assert "欢迎来到酒馆" in output
        assert "Alice" in output

    def test_handle_pc_input(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "PC开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            # PC 输入"大家好" → action result
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "Alice 环顾四周，酒馆里的冒险者们纷纷点头回应。",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "environment",
                "reason": "环境过渡",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input('"大家好"')
        assert "大家好" in output

    def test_handle_save(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{保存}")
        assert "已保存" in output

    def test_handle_view_present(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{查看在场}")
        assert "Alice" in output

    def test_handle_skill_check(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
            skills={"侦查": 60},
        )
        gl.new_game(
            "测试", "世界", pc,
            mechanics_mode="light-rules", rules_system="coc",
        )
        output = gl.handle_input("{检定 侦查}")
        assert "d100=" in output
        assert "侦查" in output

    def test_handle_skill_check_pure_narrative(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{检定 侦查}")
        assert "纯叙事模式" in output

    def test_trigger_checkpoint(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            "摘要文本",
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.trigger_checkpoint("第一章")
        assert "检查点已创建" in output
        assert gl.session is not None
        assert len(gl.session.checkpoints) == 1


class TestGameLoopConfirmation:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def _start_game(self, gl, provider):
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)

    def test_propose_checkpoint_creates_pending(self, loop):
        gl, provider = loop
        self._start_game(gl, provider)
        output = gl.propose_checkpoint("第一章结束")
        assert "待确认" in output
        assert gl.has_pending_confirmation() is True

    def test_confirm_checkpoint_executes(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            "摘要文本",
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        gl.propose_checkpoint("第一章结束")
        output = gl.handle_input("{确认}")
        assert "检查点已创建" in output
        assert gl.has_pending_confirmation() is False
        assert len(gl.session.checkpoints) == 1

    def test_reject_checkpoint_clears_pending(self, loop):
        gl, provider = loop
        self._start_game(gl, provider)
        gl.propose_checkpoint("第一章结束")
        output = gl.handle_input("{拒绝}")
        assert "已拒绝" in output
        assert gl.has_pending_confirmation() is False
        assert len(gl.session.checkpoints) == 0

    def test_input_blocked_while_pending(self, loop):
        gl, provider = loop
        self._start_game(gl, provider)
        gl.propose_checkpoint("第一章结束")
        output = gl.handle_input("大家好")
        assert "待确认" in output


class TestPlayerAbsentMode:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def test_new_game_absent_creates_session_without_pc(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "奇幻世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境描述",
                "inner_thought": None,
                "entered": ["npc_aria", "npc_bob"],
            }),
            json.dumps({
                "id": "npc_aria", "name": "Aria", "character_type": "npc",
                "personality": "温柔",
            }),
            json.dumps({
                "id": "npc_bob", "name": "Bob", "character_type": "npc",
                "personality": "豪爽",
            }),
            json.dumps({
                "next_speaker": "npc_aria",
                "reason": "开场",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        output = gl.new_game_absent("空缺测试", "奇幻世界")
        assert gl.session is not None
        assert gl.session.mode == "player-absent"
        assert gl.session.name == "空缺测试"
        assert gl._pc_id is None
        assert "初始环境描述" in output
        assert "npc_aria" in gl.present_characters
        assert "npc_bob" in gl.present_characters

    def test_continue_in_absent_mode_generates_npc_action(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境",
                "inner_thought": None,
                "entered": ["npc_aria"],
            }),
            json.dumps({
                "id": "npc_aria", "name": "Aria", "character_type": "npc",
                "personality": "温柔",
            }),
            json.dumps({
                "next_speaker": "npc_aria",
                "reason": "开场",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            json.dumps({
                "character_id": "npc_aria",
                "dialogue": "你好，旅人。",
                "action": "微笑",
                "inner_thought": "期待新故事",
            }),
            # NPC 动作结果
            json.dumps({
                "character_id": "npc_aria",
                "dialogue": None,
                "action": "Aria 露出温柔的微笑，眼中闪过一丝期待的光芒。",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "environment",
                "reason": "环境过渡",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game_absent("空缺测试", "世界")
        output = gl.handle_input("{继续}")
        assert "你好，旅人" in output
        assert "环境" in output

    def test_skill_check_disabled_in_absent_mode(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境",
                "inner_thought": None,
                "entered": ["npc_aria"],
            }),
            json.dumps({
                "id": "npc_aria", "name": "Aria", "character_type": "npc",
                "personality": "温柔",
            }),
            json.dumps({
                "next_speaker": "npc_aria",
                "reason": "开场",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game_absent("空缺测试", "世界")
        output = gl.handle_input("{检定 侦查}")
        assert "玩家空缺模式" in output
        assert "不启用" in output

    def test_pc_input_treated_as_environment_in_absent_mode(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境",
                "inner_thought": None,
                "entered": ["npc_aria"],
            }),
            json.dumps({
                "id": "npc_aria", "name": "Aria", "character_type": "npc",
                "personality": "温柔",
            }),
            json.dumps({
                "next_speaker": "npc_aria",
                "reason": "开场",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            json.dumps({
                "next_speaker": "npc_aria",
                "reason": "继续",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game_absent("空缺测试", "世界")
        output = gl.handle_input("突然下起了暴雨")
        assert "突然下起了暴雨" in output
        assert "环境" in output


class TestCheckEmbeddedInNarrative:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def _start_light_rules_game(self, gl, provider):
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始环境",
                "inner_thought": None,
                "entered": ["pc_alice", "guard"],
            }),
            json.dumps({
                "id": "guard", "name": "Guard", "character_type": "npc",
                "personality": "严肃",
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "PC开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
            personality="机智", skills={"说服": 3},
        )
        gl.new_game(
            "测试", "世界", pc,
            mechanics_mode="light-rules", rules_system="d20",
        )

    def test_pc_action_triggers_check_and_generates_narrative(self, loop):
        gl, provider = loop
        self._start_light_rules_game(gl, provider)
        provider.set_responses([
            json.dumps({
                "needed": True,
                "skill": "说服",
                "dc": 15,
                "reason": "守卫警觉",
            }),
            json.dumps({
                "character_id": "pc_alice",
                "dialogue": "守卫大人，行个方便",
                "action": "递上金币，守卫犹豫后让开了路",
                "inner_thought": "幸好准备充分",
            }),
            json.dumps({
                "next_speaker": "guard",
                "reason": "守卫反应",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        output = gl.handle_input("我说服守卫放行")
        assert "让开了路" in output
        assert "[检定]" in output or "检定" in output

    def test_pc_action_without_check_goes_normal_path(self, loop):
        gl, provider = loop
        self._start_light_rules_game(gl, provider)
        provider.set_responses([
            json.dumps({
                "needed": False,
                "skill": "",
                "dc": 0,
                "reason": "普通对话",
            }),
            # PC 动作结果
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "守卫抬头看了Alice一眼，点了点头。",
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "guard",
                "reason": "守卫回应",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        output = gl.handle_input("我和守卫打招呼")
        assert "打招呼" in output or "guard" in output.lower() or "判断" in output

    def test_check_failure_reflected_in_narrative(self, loop):
        gl, provider = loop
        self._start_light_rules_game(gl, provider)
        provider.set_responses([
            json.dumps({
                "needed": True,
                "skill": "说服",
                "dc": 20,
                "reason": "守卫极其警觉",
            }),
            json.dumps({
                "character_id": "pc_alice",
                "dialogue": "守卫大人，行个方便",
                "action": "守卫冷笑，挥手拒绝",
                "inner_thought": "糟了，他不吃这套",
            }),
            json.dumps({
                "next_speaker": "guard",
                "reason": "守卫反应",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        output = gl.handle_input("我说服守卫放行")
        assert "拒绝" in output or "失败" in output


class TestModuleGameStart:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def test_new_game_with_module_loads_world_and_npcs(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "next_speaker": "gareth_ironpot",
                "reason": "酒馆老板迎客",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(
            id="pc_main", name="冒险者", character_type="pc",
            personality="好奇", skills={"察觉": 3},
        )
        output = gl.new_game_with_module(
            name="模组测试",
            module_name="铁炉镇冒险",
            pc_profile=pc,
        )
        assert gl.session is not None
        assert gl.session.mode == "player-present"
        assert gl.session.campaign_background is not None
        assert "铁炉镇" in gl.session.campaign_background.world_setting
        all_ids = [c.id for c in gl._characters.get_all_characters()]
        assert "gareth_ironpot" in all_ids
        assert "炉火" in output or "酒馆" in output

    def test_new_game_with_module_imports_all_characters(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "next_speaker": "pc_main",
                "reason": "PC开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(
            id="pc_main", name="PC", character_type="pc",
        )
        gl.new_game_with_module("模组测试", "铁炉镇冒险", pc)
        all_ids = [c.id for c in gl._characters.get_all_characters()]
        assert "gareth_ironpot" in all_ids
        assert "thorin_steelforge" in all_ids
        assert "elara_moonshadow" in all_ids

    def test_new_game_with_module_not_found(self, loop):
        gl, provider = loop
        pc = CharacterProfile(id="pc", name="PC", character_type="pc")
        output = gl.new_game_with_module("测试", "不存在的模组", pc)
        assert "未找到" in output or "不存在" in output

    def test_new_game_with_module_absent_mode(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "next_speaker": "mayuko_inoue",
                "reason": "情报贩子登场",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        output = gl.new_game_with_module(
            name="模组空缺测试",
            module_name="新东京暗流",
        )
        assert gl.session.mode == "player-absent"
        assert gl._pc_id is None
        all_ids = [c.id for c in gl._characters.get_all_characters()]
        assert "mayuko_inoue" in all_ids
        assert "新东京" in gl.session.campaign_background.world_setting


class TestCheckpointSystem:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def _start_game(self, gl, provider):
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)

    def test_checkpoint_directive_creates_pending(self, loop):
        gl, provider = loop
        self._start_game(gl, provider)
        output = gl.handle_input("{检查点}")
        assert "待确认" in output
        assert gl.has_pending_confirmation() is True

    def test_checkpoint_directive_with_label(self, loop):
        gl, provider = loop
        self._start_game(gl, provider)
        output = gl.handle_input("{检查点 第一章结束}")
        assert "待确认" in output
        assert "第一章结束" in output
        assert gl.has_pending_confirmation() is True

    def test_confirm_checkpoint_with_cleanup(self, loop):
        from rpg_chat.types import ActionUnit
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice", "npc_bob"],
            }),
            json.dumps({
                "id": "npc_bob", "name": "Bob", "character_type": "npc",
                "personality": "狡猾",
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            "摘要文本",
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        gl.handle_input("{检查点}")
        output = gl.handle_input("{确认 npc_bob}")
        assert "检查点已创建" in output
        assert gl.has_pending_confirmation() is False
        bob_ctx = gl._characters.get_context("npc_bob")
        assert len(bob_ctx.action_units) == 0

    def test_checkpoint_refreshes_fortune_then_npc_has_it(self, loop):
        gl, provider = loop
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice", "npc_bob"],
            }),
            json.dumps({
                "id": "npc_bob", "name": "Bob", "character_type": "npc",
                "personality": "胆小",
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            "摘要文本",
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        gl.handle_input("{检查点}")
        gl.handle_input("{确认}")
        bob_ctx = gl._characters.get_context("npc_bob")
        from rpg_chat.fortune import FortuneLevel
        assert bob_ctx.fortune in [level.value for level in FortuneLevel]


class TestModifyCharacter:
    @pytest.fixture
    def loop(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(
            max_consecutive_characters=5,
            sanity_check_interval=10,
            auto_chain_enabled=False,
        )
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider, cs

    def test_modify_character_string_field(self, loop):
        """修改角色的字符串字段"""
        gl, provider, cs = loop
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
            personality="勇敢的冒险者",
        )
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{修改角色 pc_alice personality 谨慎的学者}")
        assert "已修改" in output
        updated = cs.get_profile("pc_alice")
        assert updated.personality == "谨慎的学者"

    def test_modify_character_dict_field(self, loop):
        """使用 JSON 值修改角色的 dict 字段（如 skills）"""
        gl, provider, cs = loop
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
            skills={"潜行": 40},
        )
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input(
            '{修改角色 pc_alice skills {"潜行": 70, "侦查": 50}}'
        )
        assert "已修改" in output
        updated = cs.get_profile("pc_alice")
        assert updated.skills == {"潜行": 70, "侦查": 50}

    def test_modify_character_nonexistent(self, loop):
        """修改不存在的角色应返回错误"""
        gl, provider, cs = loop
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
        )
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{修改角色 npc_ghost personality 幽灵}")
        assert "不存在" in output

    def test_modify_character_invalid_syntax(self, loop):
        """不完整的指令应返回用法提示"""
        gl, provider, cs = loop
        pc = CharacterProfile(
            id="pc_alice", name="Alice", character_type="pc",
        )
        provider.set_responses([
            json.dumps({
                "world_setting": "世界",
                "factions": [], "history": [],
                "important_locations": [], "initial_situation": "",
            }),
            json.dumps({
                "character_id": None,
                "dialogue": None,
                "action": "初始",
                "inner_thought": None,
                "entered": ["pc_alice"],
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{修改角色 pc_alice}")
        assert "用法" in output
