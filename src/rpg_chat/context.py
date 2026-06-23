from typing import Optional

from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.types import CampaignBackground


class ContextAssembler:
    def __init__(
        self,
        character_store: CharacterStore,
        dialogue_log: DialogueLog,
        environment_store: EnvironmentStore,
        scene_tracker: SceneTracker,
    ):
        self._character_store = character_store
        self._dialogue_log = dialogue_log
        self._environment_store = environment_store
        self._scene_tracker = scene_tracker
        self._campaign_background: Optional[CampaignBackground] = None

    def set_campaign_background(self, bg: CampaignBackground):
        self._campaign_background = bg

    def assemble_for_character(self, character_id: str) -> dict:
        profile = self._character_store.get_profile(character_id)
        ctx = self._character_store.get_context(character_id)

        own_action_units = ctx.action_units
        own_inner_thoughts = [
            au for au in own_action_units if au.inner_thought
        ]

        public_dialogue = self._dialogue_log.history()

        visible_env = self._environment_store.visible_entries_for(
            character_id
        )

        present = self._scene_tracker.get_present()

        return {
            "profile": profile,
            "own_action_units": own_action_units,
            "public_dialogue_history": public_dialogue,
            "visible_environment": visible_env,
            "present_characters": present,
        }

    def assemble_for_judgment(self) -> dict:
        all_profiles = self._character_store.get_all_characters()

        all_contexts = {}
        for char in all_profiles:
            ctx = self._character_store.get_context(char.id)
            all_contexts[char.id] = ctx

        public_dialogue = self._dialogue_log.history()

        all_env = self._environment_store.all_entries()

        present = self._scene_tracker.get_present()

        campaign_summary = ""
        if self._campaign_background:
            parts = [f"世界: {self._campaign_background.world_setting}"]
            if self._campaign_background.power_system:
                parts.append(f"力量体系: {self._campaign_background.power_system[:500]}")
            parts.append(f"当前场景: {self._campaign_background.initial_situation}")
            campaign_summary = "\n".join(parts)

        return {
            "all_profiles": all_profiles,
            "all_contexts": all_contexts,
            "public_dialogue_history": public_dialogue,
            "all_environment": all_env,
            "present_characters": present,
            "campaign_summary": campaign_summary,
        }
