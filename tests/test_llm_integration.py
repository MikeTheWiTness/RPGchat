import json
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from rpg_chat.llm_openai import OpenAIProvider

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


@pytest.mark.skipif(not API_KEY, reason="需要 DEEPSEEK_API_KEY")
class TestLLMIntegration:
    @pytest.fixture
    def provider(self):
        return OpenAIProvider()

    def test_basic_connectivity(self, provider):
        result = provider.complete("请用JSON格式回答: {\"greeting\": \"你好\", \"role\": \"assistant\"}")
        assert result is not None
        assert len(result) > 0
        data = json.loads(result)
        assert "greeting" in data or "你好" in result

    def test_npc_action_unit_format(self, provider):
        prompt = """你正在扮演 TRPG 角色 "Goblin Thief"。
性格: 胆小但狡猾的小偷

当前场景: 酒馆角落
请生成该角色的下一动作单元，返回 JSON:
{"character_id": "goblin_thief", "dialogue": "对话（可选）", "action": "行动描述（可选）", "inner_thought": "内心活动（可选）", "audience": null, "entered": null, "left": null}
要求 dialogue/action/inner_thought 至少一项不为空，只返回 JSON。"""
        result = provider.complete(prompt)
        print(f"NPC Response: {result}")
        data = json.loads(result)
        assert data.get("character_id") is not None
        has_content = data.get("dialogue") or data.get("action") or data.get("inner_thought")
        assert has_content, f"至少一项不为空: {data}"

    def test_judgment_format(self, provider):
        prompt = """作为 GM，判断接下来由谁发言/行动。
在场人物: pc_alice, npc_bob
最近对话: 
[pc_alice]: 你好，Bob
[npc_bob]: 欢迎来到铁炉堡

返回 JSON:
{"next_speaker": "角色id或environment", "reason": "理由", "force_environment": false, "corrected_present_characters": null}
只返回 JSON。"""
        result = provider.complete(prompt)
        print(f"Judgment Response: {result}")
        data = json.loads(result)
        assert "next_speaker" in data
        assert data["next_speaker"] in ("pc_alice", "npc_bob", "environment")

    def test_environment_action_unit_format(self, provider):
        prompt = """你是 TRPG 场景叙述者。当前在场: pc_alice, npc_bob
生成环境动作单元，返回 JSON:
{"character_id": null, "dialogue": null, "action": "环境描写", "inner_thought": null, "audience": null, "entered": null, "left": null}
只返回 JSON。"""
        result = provider.complete(prompt)
        print(f"Environment Response: {result}")
        data = json.loads(result)
        assert "action" in data
        assert data["action"] is not None
        assert len(data["action"]) > 0

    def test_campaign_expansion_format(self, provider):
        prompt = """请将以下简短描述扩展为结构化世界观 JSON:
"一个中世纪奇幻世界，北方王国和南方帝国正在交战"

返回 JSON:
{"world_setting": "概述", "factions": [{"name": "势力名", "description": "描述"}], "history": [], "important_locations": [], "initial_situation": "开局场景"}
只返回 JSON。"""
        result = provider.complete(prompt)
        print(f"Campaign Response: {result}")
        data = json.loads(result)
        assert "world_setting" in data
        assert len(data.get("factions", [])) > 0
