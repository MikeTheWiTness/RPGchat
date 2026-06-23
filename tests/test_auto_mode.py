import json
import pytest
from rpg_chat.llm import MockLLMProvider, LLMGateway
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.game_loop import GameLoop, GameLoopConfig
from rpg_chat.auto_mode import AutoModeController
from rpg_chat.types import CharacterProfile


class TestAutoMode:
    @pytest.fixture
    def setup(self):
        provider = MockLLMProvider()
        gateway = LLMGateway(provider)
        cs = CharacterStore()
        dl = DialogueLog()
        es = EnvironmentStore()
        st = SceneTracker()
        ca = ContextAssembler(cs, dl, es, st)
        config = GameLoopConfig(auto_chain_enabled=False)
        gl = GameLoop(gateway, cs, dl, es, st, ca, config)
        return gl, provider

    def test_start_auto_mode(self, setup):
        gl, provider = setup
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
                "entered": ["npc_1"],
            }),
            json.dumps({
                "next_speaker": "npc_1",
                "reason": "npc先说话",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            json.dumps({
                "character_id": "npc_1",
                "dialogue": "这天终于来了...",
                "action": "叹气",
                "inner_thought": "新的冒险者",
            }),
            json.dumps({
                "next_speaker": "environment",
                "reason": "环境过渡",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])

        gl.new_game(
            "自动测试", "世界",
            CharacterProfile(id="pc", name="PC", character_type="pc"),
        )

        controller = AutoModeController(gl)
        output = controller.start()
        assert controller.is_running is True
        assert controller.is_paused is False

    def test_pause_and_resume(self, setup):
        gl, provider = setup
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
                "next_speaker": "pc",
                "reason": "PC开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])

        gl.new_game(
            "自动测试", "世界",
            CharacterProfile(id="pc", name="PC", character_type="pc"),
        )

        controller = AutoModeController(gl)
        controller.start()
        output = controller.pause()
        assert controller.is_paused is True
        assert "已暂停" in output
        controller.resume()
        assert controller.is_paused is False

    def test_pause_interval(self, setup):
        gl, provider = setup
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
                "entered": ["npc_1"],
            }),
            json.dumps({
                "next_speaker": "npc_1",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
            json.dumps({
                "character_id": "npc_1",
                "dialogue": "第一句",
                "action": None,
                "inner_thought": None,
            }),
            json.dumps({
                "next_speaker": "pc",
                "reason": "轮到pc",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])

        gl.new_game(
            "自动测试", "世界",
            CharacterProfile(id="pc", name="PC", character_type="pc"),
        )

        controller = AutoModeController(gl, pause_interval=1)
        output = controller.start()
        assert controller.is_paused is True
        assert "自动暂停" in output

    def test_issue_directive_in_auto_mode(self, setup):
        gl, provider = setup
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
                "next_speaker": "pc",
                "reason": "开始",
                "force_environment": False,
                "corrected_present_characters": None,
            }),
        ])

        gl.new_game(
            "自动测试", "世界",
            CharacterProfile(id="pc", name="PC", character_type="pc"),
        )

        controller = AutoModeController(gl)
        controller.start()
        output = controller.issue_directive("保存")
        assert "已保存" in output
