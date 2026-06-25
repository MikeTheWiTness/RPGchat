from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConfirmationType(str, Enum):
    SCENE_CHANGE = "scene_change"
    CHECKPOINT = "checkpoint"
    TIME_SKIP = "time_skip"
    PROFILE_CHANGE = "profile_change"


@dataclass
class ConfirmationRequest:
    id: str
    type: ConfirmationType
    description: str
    payload: dict = field(default_factory=dict)
    status: str = "pending"


class ConfirmationManager:
    def __init__(self):
        self._pending: Optional[ConfirmationRequest] = None
        self._history: list[ConfirmationRequest] = []

    def propose(
        self,
        type: ConfirmationType,
        description: str,
        payload: dict | None = None,
    ) -> ConfirmationRequest:
        if self._pending is not None:
            raise ValueError("已有待确认请求，请先处理")
        req = ConfirmationRequest(
            id=f"conf_{len(self._history) + 1}",
            type=type,
            description=description,
            payload=payload or {},
        )
        self._pending = req
        return req

    def get_pending(self) -> Optional[ConfirmationRequest]:
        return self._pending

    def has_pending(self) -> bool:
        return self._pending is not None

    def clear(self) -> None:
        if self._pending is not None:
            self._history.append(self._pending)
            self._pending = None

    def confirm(self, request_id: str) -> ConfirmationRequest:
        return self._resolve(request_id, "confirmed")

    def reject(self, request_id: str) -> ConfirmationRequest:
        return self._resolve(request_id, "rejected")

    def _resolve(self, request_id: str, status: str) -> ConfirmationRequest:
        req = self._pending
        if req is None or req.id != request_id:
            raise ValueError(f"无待确认请求: {request_id}")
        req.status = status
        self._history.append(req)
        self._pending = None
        return req
