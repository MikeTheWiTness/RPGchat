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

        perceived_actions = self._get_perceived_actions(character_id)
        all_profiles = self._character_store.get_all_characters()

        campaign_summary = ""
        if self._campaign_background:
            parts = [f"世界: {self._campaign_background.world_setting[:500]}"]
            scene = self._campaign_background.current_scene or self._campaign_background.initial_situation
            parts.append(f"当前场景: {scene}")
            campaign_summary = "\n".join(parts)

        return {
            "profile": profile,
            "own_action_units": own_action_units,
            "public_dialogue_history": public_dialogue,
            "visible_environment": visible_env,
            "present_characters": present,
            "fortune": ctx.fortune,
            "perceived_actions": perceived_actions,
            "all_profiles": all_profiles,
            "campaign_summary": campaign_summary,
        }

    def _get_perceived_actions(self, character_id: str) -> list:
        """获取角色能感知到的所有动作单元（按 audience 过滤）"""
        result = []
        all_profiles = self._character_store.get_all_characters()
        for profile in all_profiles:
            ctx = self._character_store.get_context(profile.id)
            for au in ctx.action_units:
                if self._is_action_visible_to(au, character_id):
                    result.append(au)
        return result

    @staticmethod
    def _is_action_visible_to(au, character_id: str) -> bool:
        # 自己的动作始终可见
        if au.character_id == character_id:
            return True
        # audience 为 None 表示公开
        if au.audience is None:
            return True
        # audience 列表中包含目标角色
        return character_id in au.audience

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
            parts = [f"世界: {self._campaign_background.world_setting[:1000]}"]
            scene = self._campaign_background.current_scene or self._campaign_background.initial_situation
            parts.append(f"当前场景: {scene}")
            campaign_summary = "\n".join(parts)

        return {
            "all_profiles": all_profiles,
            "all_contexts": all_contexts,
            "public_dialogue_history": public_dialogue,
            "all_environment": all_env,
            "present_characters": present,
            "campaign_summary": campaign_summary,
        }
