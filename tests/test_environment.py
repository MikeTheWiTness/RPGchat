import pytest
from rpg_chat.types import EnvironmentEntry
from rpg_chat.environment import DialogueLog, EnvironmentStore


class TestDialogueLog:
    def test_append_and_history(self):
        log = DialogueLog()
        log.append("pc_alice", "你好")
        log.append("npc_bob", "欢迎")
        history = log.history()
        assert len(history) == 2
        assert history[0].character_id == "pc_alice"
        assert history[0].dialogue == "你好"
        assert history[1].character_id == "npc_bob"
        assert history[1].dialogue == "欢迎"

    def test_append_empty_dialogue_skipped(self):
        log = DialogueLog()
        log.append("pc_alice", "")
        log.append("pc_alice", "   ")
        assert len(log.history()) == 0

    def test_timestamps_are_in_order(self):
        log = DialogueLog()
        log.append("pc_alice", "第一句")
        log.append("npc_bob", "第二句")
        history = log.history()
        assert history[0].timestamp <= history[1].timestamp

    def test_empty_history(self):
        log = DialogueLog()
        assert log.history() == []


class TestEnvironmentStore:
    def test_add_entry(self):
        store = EnvironmentStore()
        entry = store.add_entry("大门紧闭", ["pc_alice", "npc_bob"])
        assert entry.id is not None
        assert entry.description == "大门紧闭"
        assert entry.visible_to == ["pc_alice", "npc_bob"]

    def test_visible_entries_for(self):
        store = EnvironmentStore()
        store.add_entry("大门紧闭", ["pc_alice", "npc_bob"])
        store.add_entry("暗门", ["pc_alice"])
        store.add_entry("桌上的金币", ["npc_bob"])

        alice_entries = store.visible_entries_for("pc_alice")
        assert len(alice_entries) == 2
        assert {e.description for e in alice_entries} == {"大门紧闭", "暗门"}

        bob_entries = store.visible_entries_for("npc_bob")
        assert len(bob_entries) == 2
        assert {e.description for e in bob_entries} == {"大门紧闭", "桌上的金币"}

        charlie_entries = store.visible_entries_for("npc_charlie")
        assert charlie_entries == []

    def test_update_entry(self):
        store = EnvironmentStore()
        entry = store.add_entry("大门紧闭", ["pc_alice"])
        store.update_entry(entry.id, {"description": "大门敞开"})
        e = store.all_entries()[0]
        assert e.description == "大门敞开"

    def test_remove_entry(self):
        store = EnvironmentStore()
        entry = store.add_entry("大门紧闭", ["pc_alice"])
        store.remove_entry(entry.id)
        assert store.all_entries() == []

    def test_all_entries(self):
        store = EnvironmentStore()
        store.add_entry("A", ["pc_alice"])
        store.add_entry("B", ["pc_alice"])
        assert len(store.all_entries()) == 2
