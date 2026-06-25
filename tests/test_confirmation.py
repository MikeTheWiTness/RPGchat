import pytest

from rpg_chat.confirmation import (
    ConfirmationManager,
    ConfirmationRequest,
    ConfirmationType,
)


class TestConfirmationManager:
    def test_propose_scene_change_creates_pending_request(self):
        cm = ConfirmationManager()
        req = cm.propose(
            ConfirmationType.SCENE_CHANGE,
            "从酒馆切换到街道",
            {"target_scene": "街道"},
        )
        assert req.type == ConfirmationType.SCENE_CHANGE
        assert req.description == "从酒馆切换到街道"
        assert req.payload == {"target_scene": "街道"}
        assert req.status == "pending"
        assert cm.get_pending() is req

    def test_confirm_pending_request_clears_pending(self):
        cm = ConfirmationManager()
        req = cm.propose(
            ConfirmationType.CHECKPOINT, "第一章结束", {"stage_label": "第一章"}
        )
        confirmed = cm.confirm(req.id)
        assert confirmed.status == "confirmed"
        assert cm.get_pending() is None

    def test_reject_pending_request_clears_pending(self):
        cm = ConfirmationManager()
        req = cm.propose(
            ConfirmationType.TIME_SKIP, "三天后", {"duration": "3天"}
        )
        rejected = cm.reject(req.id)
        assert rejected.status == "rejected"
        assert cm.get_pending() is None

    def test_has_pending_reflects_state(self):
        cm = ConfirmationManager()
        assert cm.has_pending() is False
        cm.propose(ConfirmationType.PROFILE_CHANGE, "性格转变", {})
        assert cm.has_pending() is True
        cm.clear()
        assert cm.has_pending() is False

    def test_propose_while_pending_raises(self):
        cm = ConfirmationManager()
        cm.propose(ConfirmationType.SCENE_CHANGE, "切换A", {})
        with pytest.raises(ValueError, match="已有待确认请求"):
            cm.propose(ConfirmationType.CHECKPOINT, "切换B", {})

    def test_confirm_nonexistent_id_raises(self):
        cm = ConfirmationManager()
        with pytest.raises(ValueError, match="无待确认请求"):
            cm.confirm("conf_999")

    def test_reject_nonexistent_id_raises(self):
        cm = ConfirmationManager()
        with pytest.raises(ValueError, match="无待确认请求"):
            cm.reject("conf_999")

    def test_confirm_already_resolved_raises(self):
        cm = ConfirmationManager()
        req = cm.propose(ConfirmationType.CHECKPOINT, "检查点", {})
        cm.confirm(req.id)
        with pytest.raises(ValueError, match="无待确认请求"):
            cm.confirm(req.id)

    def test_all_four_types_proposable_with_payload(self):
        cm = ConfirmationManager()
        cases = [
            (ConfirmationType.SCENE_CHANGE, {"target_scene": "森林"}),
            (ConfirmationType.CHECKPOINT, {"stage_label": "第二章"}),
            (ConfirmationType.TIME_SKIP, {"duration": "一周"}),
            (ConfirmationType.PROFILE_CHANGE, {"character_id": "npc_1", "field": "personality"}),
        ]
        for ctype, payload in cases:
            cm = ConfirmationManager()
            req = cm.propose(ctype, "描述", payload)
            assert req.type == ctype
            assert req.payload == payload
