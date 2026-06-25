import pytest
from rpg_chat.scene import SceneTracker
from rpg_chat.types import ActionUnit


class TestSceneTracker:
    @pytest.fixture
    def tracker(self):
        return SceneTracker()

    def test_initial_state_empty(self, tracker):
        assert tracker.get_present() == []
        assert tracker.action_count_since_env == 0
        assert tracker.total_action_count == 0

    def test_entered_adds_characters(self, tracker):
        au = ActionUnit(character_id="npc_1", entered=["npc_2", "npc_3"])
        tracker.process_action_unit(au)
        assert "npc_2" in tracker.get_present()
        assert "npc_3" in tracker.get_present()

    def test_left_removes_characters(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="env", entered=["npc_2", "npc_3"])
        )
        tracker.process_action_unit(
            ActionUnit(character_id="npc_2", left=["npc_2"])
        )
        present = tracker.get_present()
        assert "npc_2" not in present
        assert "npc_3" in present

    def test_default_audience_is_all_present(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="env", entered=["pc", "npc_a", "npc_b"])
        )
        au = ActionUnit(character_id="npc_a", dialogue="你好")
        audience = tracker.resolve_audience(au)
        assert audience == {"pc", "npc_a", "npc_b"}

    def test_explicit_audience_narrows(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="env", entered=["pc", "npc_a", "npc_b"])
        )
        au = ActionUnit(
            character_id="npc_a", dialogue="悄悄话", audience=["pc"]
        )
        audience = tracker.resolve_audience(au)
        assert audience == {"pc"}

    def test_audience_out_of_range_raises(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="env", entered=["pc"])
        )
        au = ActionUnit(
            character_id="npc_a", audience=["pc", "npc_not_here"]
        )
        with pytest.raises(ValueError, match="不在场景中"):
            tracker.resolve_audience(au)

    def test_apply_correction(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="env", entered=["pc", "npc_a"])
        )
        tracker.apply_correction(["pc", "npc_b"])
        assert set(tracker.get_present()) == {"pc", "npc_b"}

    def test_action_count_tracking(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="npc_a", dialogue="1")
        )
        tracker.process_action_unit(
            ActionUnit(character_id="npc_b", dialogue="2")
        )
        assert tracker.total_action_count == 2
        assert tracker.action_count_since_env == 2

    def test_env_resets_counter(self, tracker):
        tracker.process_action_unit(
            ActionUnit(character_id="npc_a", dialogue="1")
        )
        tracker.process_action_unit(
            ActionUnit(character_id=None, action="环境描写")
        )
        assert tracker.action_count_since_env == 0
        assert tracker.total_action_count == 2
