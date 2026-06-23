from rpg_chat.game_loop import GameLoop
from rpg_chat.types import ActionUnit, AgentDirective


class AutoModeController:
    def __init__(
        self, game_loop: GameLoop, pause_interval: int | None = None
    ):
        self._loop = game_loop
        self._pause_interval = pause_interval
        self._action_count = 0
        self._paused = False
        self._running = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> str:
        self._running = True
        self._paused = False
        self._action_count = 0
        return self._step()

    def pause(self) -> str:
        self._paused = True
        return "[系统] 自动推演已暂停"

    def resume(self) -> str:
        if not self._running:
            return "[系统] 自动推演未运行"
        self._paused = False
        return self._step()

    def step(self) -> str:
        if not self._running:
            return "[系统] 自动推演未运行"
        return self._step()

    def issue_directive(self, directive_text: str) -> str:
        return self._loop.handle_input(f"{{{directive_text}}}")

    def _step(self) -> str:
        if self._paused:
            return "[系统] 自动推演已暂停"

        result = self._loop.handle_input("{继续}")
        self._action_count += 1
        self._running = True

        if (
            self._pause_interval is not None
            and self._action_count % self._pause_interval == 0
        ):
            self._paused = True
            result += "\n[系统] 已达到暂停间隔，自动暂停。"

        return result
