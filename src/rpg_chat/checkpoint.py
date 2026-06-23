from datetime import datetime, timezone

from rpg_chat.types import (
    ActionUnit,
    CharacterContext,
    CheckpointSummary,
    EnvironmentEntry,
    GameSession,
)
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.llm import LLMGateway


class CheckpointManager:
    def __init__(
        self,
        llm: LLMGateway,
        character_store: CharacterStore,
        dialogue_log: DialogueLog,
        environment_store: EnvironmentStore,
    ):
        self._llm = llm
        self._character_store = character_store
        self._dialogue_log = dialogue_log
        self._environment_store = environment_store

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
            checkpoint.character_updates[char_id] = updatable

        env_entries = self._environment_store.all_entries()
        checkpoint.environment_state = "\n".join(
            e.description for e in env_entries[-5:]
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

    @staticmethod
    def restore_from_checkpoint(
        session: GameSession
    ) -> GameSession:
        return session
