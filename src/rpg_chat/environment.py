import uuid
from datetime import datetime, timezone

from rpg_chat.types import DialogueEntry, EnvironmentEntry


class DialogueLog:
    def __init__(self):
        self._entries: list[DialogueEntry] = []

    def append(self, character_id: str, dialogue: str):
        if not dialogue.strip():
            return
        self._entries.append(
            DialogueEntry(
                character_id=character_id,
                dialogue=dialogue,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    def history(self) -> list[DialogueEntry]:
        return list(self._entries)


class EnvironmentStore:
    def __init__(self):
        self._entries: list[EnvironmentEntry] = []

    def add_entry(
        self, description: str, visible_to: list[str]
    ) -> EnvironmentEntry:
        entry = EnvironmentEntry(
            id=str(uuid.uuid4()),
            description=description,
            visible_to=visible_to,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._entries.append(entry)
        return entry

    def visible_entries_for(
        self, character_id: str
    ) -> list[EnvironmentEntry]:
        return [e for e in self._entries if character_id in e.visible_to]

    def update_entry(self, entry_id: str, data: dict):
        for entry in self._entries:
            if entry.id == entry_id:
                for key, value in data.items():
                    if hasattr(entry, key):
                        setattr(entry, key, value)
                return

    def remove_entry(self, entry_id: str):
        self._entries = [e for e in self._entries if e.id != entry_id]

    def all_entries(self) -> list[EnvironmentEntry]:
        return list(self._entries)
