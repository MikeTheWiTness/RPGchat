import json
import os
import tempfile

import pytest

from rpg_chat.llm import MockLLMProvider, LLMGateway
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.game_loop import GameLoop, GameLoopConfig
from rpg_chat.types import CharacterProfile
from rpg_chat.persistence import load as load_game


def _j(obj):
    return json.dumps(obj, ensure_ascii=False)


def _make_action_result(action_text):
    """NPC/PC 动作结果：仅 action 字段的 JSON"""
    return _j({
        "character_id": None,
        "dialogue": None,
        "action": action_text,
        "inner_thought": None,
    })


def _make_env_au(scene_text, entered=None):
    return _j({
        "character_id": None,
        "dialogue": None,
        "action": scene_text,
        "inner_thought": None,
        "entered": entered,
        "left": None,
    })


def _make_npc_au(char_id, dialogue=None, action=None, thought=None, audience=None):
    return _j({
        "character_id": char_id,
        "dialogue": dialogue,
        "action": action,
        "inner_thought": thought,
        "audience": audience,
        "entered": None,
        "left": None,
    })


def _make_judgment(next_speaker, reason="继续", corrected=None):
    return _j({
        "next_speaker": next_speaker,
        "reason": reason,
        "force_environment": False,
        "corrected_present_characters": corrected,
    })


def _make_force_env_judgment(reason="已连续发言过多"):
    return _j({
        "next_speaker": "environment",
        "reason": reason,
        "force_environment": True,
        "corrected_present_characters": None,
    })


def _make_npc_profile(char_id, name):
    return _j({
        "id": char_id,
        "name": name,
        "character_type": "npc",
        "personality": "测试性格",
    })


class TestE2EGameFlow:
    @pytest.fixture
    def engine(self):
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

    def test_new_game_then_pc_then_npc(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "中世纪商港", "factions": [
                {"name": "商会", "description": "控制港口的商人"},
            ], "history": [], "important_locations": [
                {"name": "酒馆", "description": "冒险者聚集地"},
            ], "initial_situation": "冒险者在酒馆等待"}),

            _make_env_au("海风吹过港口，酒馆内烛光摇曳，角落里坐着几个商人。",
                         entered=["npc_bartender", "npc_merchant"]),
            _make_npc_profile("npc_bartender", "酒馆老板"),
            _make_npc_profile("npc_merchant", "商人"),
            _make_judgment("npc_bartender", "酒馆老板注意到新来的冒险者"),

            # 酒馆老板发言 + 动作
            _make_npc_au("npc_bartender", dialogue="欢迎来到海风酒馆！要来一杯吗？",
                         action="擦拭着吧台"),
            # 酒馆老板的动作结果
            _make_action_result("吧台在烛光下泛着温润的光泽，几滴冷凝水顺着杯壁滑落。"),
            _make_judgment("npc_merchant", "商人从角落打量来客"),

            # 商人发言 + 动作
            _make_npc_au("npc_merchant", dialogue="那边的冒险者，有兴趣谈笔生意吗？",
                         action="从角落站起身"),
            # 商人的动作结果
            _make_action_result("商人站起身时斗篷滑落，露出腰间鼓鼓的钱袋和一把精致的匕首。"),
            _make_judgment("pc_main", "PC应该回应商人的邀约"),
        ])

        pc = CharacterProfile(
            id="pc_main", name="Kael", character_type="pc",
            personality="正直的佣兵剑士", skills={"剑术": 70},
        )

        output = gl.new_game("测试", "中世纪商港", pc)
        assert "Kael" in output or "推测" in output or "海风" in output
        assert gl.session is not None
        assert "npc_bartender" in gl.present_characters

        output = gl.handle_input("{继续}")
        assert "欢迎" in output
        assert "npc_bartender" in output.lower() or "酒馆" in output
        # 酒馆老板有动作 → 动作结果 → 判断跳商人

        output = gl.handle_input("{继续}")
        assert "merchant" in output or "商人" in output
        # 商人有动作 → 动作结果 → 判断跳 PC

        output = gl.handle_input("{继续}")
        assert "PC" in output or "Kael" in output

        ctx = gl._characters.get_context("npc_bartender")
        assert len(ctx.action_units) >= 1

    def test_pc_dialogue_with_inner_thought(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "测试", "factions": [], "history": [],
                "important_locations": [], "initial_situation": "开始"}),
            _make_env_au("初始场景", entered=["npc_a"]),
            _make_npc_profile("npc_a", "NPC A"),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="你好"),
            _make_judgment("pc_main"),
        ])

        pc = CharacterProfile(id="pc_main", name="Hero", character_type="pc")
        gl.new_game("测试", "背景", pc)

        gl.handle_input("{继续}")

        output = gl.handle_input('【你好】（看起来很可疑）')
        assert "你好" in output

        ctx = gl._characters.get_context("pc_main")
        inner_thoughts = [au.inner_thought for au in ctx.action_units if au.inner_thought]
        assert any("可疑" in t for t in inner_thoughts)

    def test_save_load_roundtrip(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "测试", "factions": [], "history": [],
                "important_locations": [], "initial_situation": "开始"}),
            _make_env_au("初始场景", entered=["npc_a"]),
            _make_npc_profile("npc_a", "NPC A"),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="第一句"),
            _make_judgment("pc_main"),
        ])

        pc = CharacterProfile(id="pc_main", name="Tester", character_type="pc")
        gl.new_game("测试存档", "测试背景", pc)
        gl.handle_input("{继续}")

        with tempfile.TemporaryDirectory() as d:
            filepath = os.path.join(d, "test_save.json")
            gl.save_to_file(filepath)
            assert os.path.exists(filepath)

            loaded = load_game(filepath)
            assert loaded.name == "测试存档"
            assert "pc_main" in loaded.characters
            assert any("npc_a" in cid for cid in loaded.characters)
            assert loaded.campaign_background.world_setting == "测试"

    def test_skill_check_in_coc_mode(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "测试", "factions": [], "history": [],
                "important_locations": [], "initial_situation": "开始"}),
            _make_env_au("场景", entered=[]),
            _make_judgment("pc_main"),
        ])

        pc = CharacterProfile(
            id="pc_main", name="Scout", character_type="pc",
            skills={"侦查": 3},
        )
        gl.new_game("测试", "背景", pc, mechanics_mode="light-rules",
                    rules_system="d20")

        result = gl.handle_input("{检定 侦查}")
        assert "d20=" in result
        assert "侦查" in result

    def test_checkpoint_trigger(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "测试", "factions": [], "history": [],
                "important_locations": [], "initial_situation": "开始"}),
            _make_env_au("场景", entered=[]),
            _make_judgment("pc_main"),
            "第一章：冒险者们在酒馆遇见神秘老人，得知了古墓的秘密。",
        ])

        pc = CharacterProfile(id="pc_main", name="Hero", character_type="pc")
        gl.new_game("测试", "背景", pc)

        result = gl.trigger_checkpoint("第一章-古墓之谜")
        assert gl.session is not None
        assert len(gl.session.checkpoints) == 1
        checkpoint = gl.session.checkpoints[0]
        assert "酒馆" in checkpoint.summary or "古墓" in checkpoint.summary

    def test_force_environment_after_max_consecutive(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "测试", "factions": [], "history": [],
                "important_locations": [], "initial_situation": "开始"}),
            _make_env_au("初始场景", entered=["npc_a"]),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="1"),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="2"),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="3"),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="4"),
            _make_force_env_judgment("连续NPC发言已达上限"),
            _make_env_au("环境强制插入，酒馆外传来雷声"),
            _make_judgment("pc_main"),
        ])

        pc = CharacterProfile(id="pc_main", name="Hero", character_type="pc")
        gl.new_game("测试", "背景", pc)

        outputs = []
        for _ in range(5):
            out = gl.handle_input("{继续}")
            outputs.append(out)

        env_outputs = [o for o in outputs if "环境" in o or "雷声" in o]
        assert len(env_outputs) >= 1

    def test_present_characters_tracking(self, engine):
        gl, provider = engine
        provider.set_responses([
            _j({"world_setting": "测试", "factions": [], "history": [],
                "important_locations": [], "initial_situation": "开始"}),
            _make_env_au("初始场景", entered=["npc_a", "npc_b"]),
            _make_judgment("npc_a"),
            _make_npc_au("npc_a", dialogue="你好"),
            _make_judgment("pc_main"),
        ])

        pc = CharacterProfile(id="pc_main", name="Hero", character_type="pc")
        gl.new_game("测试", "背景", pc)
        gl.handle_input("{继续}")

        output = gl.handle_input("{查看在场}")
        assert "npc_a" in output or "npc_b" in output
