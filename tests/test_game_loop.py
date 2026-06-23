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
        assert "pc_alice" in output

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
                "next_speaker": "npc_bob",
                "reason": "让NPC说话",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            json.dumps({
                "character_id": "npc_bob",
                "dialogue": "欢迎来到酒馆",
                "action": "挥手",
                "inner_thought": "新来的冒险者",
            }),
            json.dumps({
                "next_speaker": "pc_alice",
                "reason": "轮到PC",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])
        pc = CharacterProfile(id="pc_alice", name="Alice", character_type="pc")
        gl.new_game("测试", "世界", pc)
        output = gl.handle_input("{继续}")
        assert "欢迎来到酒馆" in output
        assert "pc_alice" in output

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
