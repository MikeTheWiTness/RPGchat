from rpg_chat.types import ActionUnit


class SceneTracker:
    def __init__(self):
        self._present: set[str] = set()
        self.action_count_since_env = 0
        self.total_action_count = 0

    def process_action_unit(self, au: ActionUnit):
        if au.entered:
            for cid in au.entered:
                self._present.add(cid)
        if au.left:
            for cid in au.left:
                self._present.discard(cid)

        self.total_action_count += 1

        if au.character_id is None:
            self.action_count_since_env = 0
        else:
            self.action_count_since_env += 1

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
