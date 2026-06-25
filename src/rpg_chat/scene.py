from rpg_chat.types import ActionUnit, SceneState


class SceneTracker:
    def __init__(self):
        self._present: set[str] = set()
        self.action_count_since_env = 0
        self.total_action_count = 0
        self.consecutive_env_count = 0

    def process_action_unit(self, au: ActionUnit, count: bool = True):
        if au.entered:
            for cid in au.entered:
                self._present.add(cid)
        if au.left:
            for cid in au.left:
                self._present.discard(cid)

        if not count:
            return

        self.total_action_count += 1

        if au.character_id is None:
            self.action_count_since_env = 0
            self.consecutive_env_count += 1
        else:
            self.action_count_since_env += 1
            self.consecutive_env_count = 0

    def resolve_audience(self, au: ActionUnit) -> set[str]:
        if au.audience is not None:
            for cid in au.audience:
                if cid not in self._present:
                    raise ValueError(f"角色 {cid} 不在场景中")
            return set(au.audience)
        return set(self._present)

    def get_present(self) -> list[str]:
        return list(self._present)

    def add_characters(self, character_ids: list[str]):
        for cid in character_ids:
            self._present.add(cid)

    def apply_correction(self, corrected_list: list[str]):
        self._present = set(corrected_list)

    def snapshot(self) -> SceneState:
        return SceneState(
            present_characters=list(self._present),
            action_count_since_env=self.action_count_since_env,
            total_action_count=self.total_action_count,
            consecutive_env_count=self.consecutive_env_count,
        )

    def restore(self, state: SceneState):
        self._present = set(state.present_characters)
        self.action_count_since_env = state.action_count_since_env
        self.total_action_count = state.total_action_count
        self.consecutive_env_count = getattr(state, 'consecutive_env_count', 0)
