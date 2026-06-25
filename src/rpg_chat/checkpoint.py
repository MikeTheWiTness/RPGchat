from datetime import datetime, timezone

from rpg_chat.types import CheckpointSummary, GameSession
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.llm import LLMGateway
from rpg_chat.fortune import FortuneSystem


class CheckpointManager:
    def __init__(
        self,
        llm: LLMGateway,
        character_store: CharacterStore,
        dialogue_log: DialogueLog,
        environment_store: EnvironmentStore,
        fortune_system: FortuneSystem | None = None,
    ):
        self._llm = llm
        self._character_store = character_store
        self._dialogue_log = dialogue_log
        self._environment_store = environment_store
        self._fortune = fortune_system or FortuneSystem()

    def trigger_checkpoint(
        self, stage_label: str, current_context: str,
        character_profiles: dict[str, object]
    ) -> CheckpointSummary:
        summary_text = self._llm.generate_summary(current_context)

        checkpoint = CheckpointSummary(
            id=f"cp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage_label=stage_label,
            summary=summary_text,
        )

        for char_id, profile in character_profiles.items():
            updatable = {}
            if hasattr(profile, 'personality'):
                updatable['personality'] = profile.personality
            if hasattr(profile, 'notes'):
                updatable['notes'] = profile.notes
            updatable['fortune'] = self._fortune.roll_fortune().value
            checkpoint.character_updates[char_id] = updatable
            ctx = self._character_store.get_context(char_id)
            ctx.fortune = updatable['fortune']

        env_entries = self._environment_store.all_entries()
        checkpoint.environment_state = "\n".join(
            e.description for e in env_entries[-5:]
        )

        self._environment_store.cleanup_old_entries(keep=5)
        visible_to = list(character_profiles.keys())
        self._environment_store.add_entry(
            f"[检查点摘要-{stage_label}] {summary_text}", visible_to
        )

        return checkpoint

    def archive_character_contexts(
        self, checkpoint: CheckpointSummary
    ):
        for char_id in checkpoint.character_updates:
            ctx = self._character_store.get_context(char_id)
            ctx.action_units = [
                au for au in ctx.action_units
                if not hasattr(au, '_archived')
            ]

    def clean_departed_contexts(self, departed_char_ids: list[str]):
        for char_id in departed_char_ids:
            ctx = self._character_store.get_context(char_id)
            ctx.action_units = []

    @staticmethod
    def restore_from_checkpoint(
        session: GameSession
    ) -> GameSession:
        return session
