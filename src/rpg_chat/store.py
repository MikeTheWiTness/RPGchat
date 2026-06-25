from rpg_chat.types import ActionUnit, CharacterContext, CharacterProfile
import copy as _copy

class CharacterStore:
    def __init__(self):
        self._profiles: dict[str, CharacterProfile] = {}
        self._contexts: dict[str, CharacterContext] = {}
        self._counter = 0

    def create_character(self, profile: CharacterProfile) -> CharacterProfile:
        self._profiles[profile.id] = profile
        self._contexts[profile.id] = CharacterContext(character_id=profile.id)
        return profile

    def get_profile(self, character_id: str) -> CharacterProfile | None:
        return self._profiles.get(character_id)

    def get_all_characters(self) -> list[CharacterProfile]:
        return list(self._profiles.values())

    def update_profile(self, character_id: str, data: dict) -> CharacterProfile:
        profile = self._profiles.get(character_id)
        if profile is None:
            raise KeyError(f"角色 {character_id} 不存在")
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return profile

    def append_context(self, character_id: str, au: ActionUnit):
        if character_id not in self._contexts:
            self._contexts[character_id] = CharacterContext(
                character_id=character_id
            )
        self._contexts[character_id].action_units.append(au)

    def get_context(self, character_id: str) -> CharacterContext:
        return self._contexts.get(
            character_id, CharacterContext(character_id=character_id)
        )

    def create_npc_on_the_fly(
        self, name: str, description: str
    ) -> CharacterProfile:
        self._counter += 1
        profile = CharacterProfile(
            id=f"npc_{name.replace(' ', '_').lower()}_{self._counter}",
            name=name,
            character_type="npc",
            personality=f"{name}: {description}",
        )
        self.create_character(profile)
        return profile

    def snapshot_contexts(self) -> dict[str, CharacterContext]:
        return _copy.deepcopy(self._contexts)

    def restore_contexts(self, data: dict[str, CharacterContext]):
        self._contexts = _copy.deepcopy(data)
