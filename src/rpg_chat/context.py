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
        self._director_intents: list[str] = []
        self._plot_context: str = ""

    def set_campaign_background(self, bg: CampaignBackground):
        self._campaign_background = bg

    def set_director_intents(self, intents: list[str]):
        self._director_intents = list(intents)

    def set_plot_context(self, text: str):
        self._plot_context = text

    def _build_campaign_summary(self, max_setting: int = 500) -> str:
        """构建战役上下文摘要，纳入所有结构化字段。"""
        if not self._campaign_background:
            return ""
        cb = self._campaign_background
        parts = []

        parts.append(f"世界设定: {cb.world_setting[:max_setting]}")

        scene = cb.current_scene or cb.initial_situation
        if scene:
            parts.append(f"当前场景: {scene}")

        if cb.factions:
            faction_lines = [
                f"  - {f.get('name', '?')}: {f.get('description', '')[:100]}"
                for f in cb.factions
            ]
            parts.append("势力:\n" + "\n".join(faction_lines))

        if cb.history:
            hist_lines = [
                f"  - {h.get('period', '?')}: {h.get('event', '')[:100]}"
                for h in cb.history
            ]
            parts.append("历史:\n" + "\n".join(hist_lines))

        if cb.important_locations:
            loc_lines = [
                f"  - {l.get('name', '?')}: {l.get('description', '')[:100]}"
                for l in cb.important_locations
            ]
            parts.append("重要地点:\n" + "\n".join(loc_lines))

        if cb.pc_role and cb.pc_role.strip():
            parts.append(f"主角定位: {cb.pc_role}")

        if cb.mission and cb.mission.strip():
            parts.append(f"核心任务: {cb.mission}")

        if cb.party:
            party_lines = [
                f"  - {m.get('name', '?')}: {m.get('role', '')} — {m.get('description', '')}"
                for m in cb.party
            ]
            parts.append("主角团:\n" + "\n".join(party_lines))

        # 导演意图（无玩家模式）
        if self._director_intents:
            intent_str = "\n".join(f"  {i+1}. {text}" for i, text in enumerate(self._director_intents))
            parts.append(f"【导演意图 — 后续剧情方向必须遵循以下指引】\n{intent_str}")

        # 剧情大纲当前章节
        if self._plot_context:
            parts.append(f"【当前剧情阶段】\n{self._plot_context}")

        return "\n\n".join(parts)

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

        campaign_summary = self._build_campaign_summary(max_setting=400)

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

        campaign_summary = self._build_campaign_summary(max_setting=800)

        return {
            "all_profiles": all_profiles,
            "all_contexts": all_contexts,
            "public_dialogue_history": public_dialogue,
            "all_environment": all_env,
            "present_characters": present,
            "campaign_summary": campaign_summary,
        }
