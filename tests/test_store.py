import pytest
from rpg_chat.store import CharacterStore
from rpg_chat.types import CharacterProfile, ActionUnit


class TestCharacterStore:
    @pytest.fixture
    def store(self):
        return CharacterStore()

    @pytest.fixture
    def alice_profile(self):
        return CharacterProfile(
            id="pc_alice",
            name="Alice",
            character_type="pc",
            personality="勇敢的战士",
            background="出身于北方王国",
            appearance="金色长发，手持长剑",
            skills={"剑术": 70, "侦查": 50},
        )

    def test_create_character(self, store, alice_profile):
        store.create_character(alice_profile)
        assert store.get_profile("pc_alice") == alice_profile

    def test_get_profile_returns_none_for_unknown(self, store):
        assert store.get_profile("unknown") is None

    def test_get_all_characters(self, store, alice_profile):
        store.create_character(alice_profile)
        bob = CharacterProfile(id="npc_bob", name="Bob")
        store.create_character(bob)
        all_chars = store.get_all_characters()
        assert len(all_chars) == 2
        assert {c.id for c in all_chars} == {"pc_alice", "npc_bob"}

    def test_update_profile(self, store, alice_profile):
        store.create_character(alice_profile)
        store.update_profile("pc_alice", {"personality": "变得谨慎"})
        p = store.get_profile("pc_alice")
        assert p.personality == "变得谨慎"
        assert p.background == "出身于北方王国"

    def test_update_profile_raises_for_unknown(self, store):
        with pytest.raises(KeyError, match="角色 unknown 不存在"):
            store.update_profile("unknown", {"name": "X"})

    def test_append_context(self, store, alice_profile):
        store.create_character(alice_profile)
        au = ActionUnit(
            character_id="pc_alice",
            dialogue="你好",
            action="挥手",
        )
        store.append_context("pc_alice", au)
        ctx = store.get_context("pc_alice")
        assert len(ctx.action_units) == 1
        assert ctx.action_units[0].dialogue == "你好"
        assert ctx.action_units[0].action == "挥手"

    def test_append_context_multiple(self, store, alice_profile):
        store.create_character(alice_profile)
        au1 = ActionUnit(character_id="pc_alice", dialogue="第一句")
        au2 = ActionUnit(character_id="pc_alice", dialogue="第二句")
        store.append_context("pc_alice", au1)
        store.append_context("pc_alice", au2)
        ctx = store.get_context("pc_alice")
        assert len(ctx.action_units) == 2

    def test_get_context_for_new_character(self, store, alice_profile):
        store.create_character(alice_profile)
        ctx = store.get_context("pc_alice")
        assert ctx.character_id == "pc_alice"
        assert ctx.action_units == []

    def test_create_npc_on_the_fly(self, store):
        profile = store.create_npc_on_the_fly("Goblin", "一只绿色皮肤的小怪物")
        assert profile.name == "Goblin"
        assert profile.character_type == "npc"
        assert "Goblin" in profile.personality
        assert store.get_profile(profile.id) is not None

    def test_create_npc_generates_unique_id(self, store):
        p1 = store.create_npc_on_the_fly("Guard A", "卫兵")
        p2 = store.create_npc_on_the_fly("Guard B", "另一个卫兵")
        assert p1.id != p2.id
