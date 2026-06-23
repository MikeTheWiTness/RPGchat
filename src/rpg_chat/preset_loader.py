import json
import os
from pathlib import Path
from typing import Optional

from rpg_chat.types import CharacterProfile, CampaignBackground


_PRESETS_DIR = Path(__file__).parent.parent.parent / "presets"
_CHARACTERS_DIR = _PRESETS_DIR / "characters"
_WORLDS_DIR = _PRESETS_DIR / "worlds"


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_character(name_or_path: str) -> Optional[CharacterProfile]:
    path = Path(name_or_path)
    if path.is_absolute() and path.exists() and path.suffix == ".json":
        return _load_character_from_file(path)

    name = name_or_path.replace(".json", "")
    candidate = _CHARACTERS_DIR / f"{name}.json"
    if candidate.exists():
        return _load_character_from_file(candidate)

    for f in _CHARACTERS_DIR.glob("*.json"):
        if f.stem == name:
            return _load_character_from_file(f)

    return None


def _load_character_from_file(path: Path) -> CharacterProfile:
    data = _read_json(path)
    return CharacterProfile(
        id=data.get("id", path.stem),
        name=data.get("name", path.stem),
        character_type=data.get("character_type", "npc"),
        personality=data.get("personality", ""),
        background=data.get("background", ""),
        appearance=data.get("appearance", ""),
        skills=data.get("skills", {}),
        attributes=data.get("attributes", {}),
        relationships=data.get("relationships", {}),
        notes=data.get("notes", ""),
        physique=data.get("physique", {}),
        identity=data.get("identity", {}),
        clothing=data.get("clothing", ""),
        behavior=data.get("behavior", {}),
        intimate_features=data.get("intimate_features", ""),
    )


def list_characters() -> list[str]:
    if not _CHARACTERS_DIR.exists():
        return []
    return sorted(
        f.stem for f in _CHARACTERS_DIR.glob("*.json")
    )


def load_world(name_or_path: str) -> Optional[CampaignBackground]:
    path = Path(name_or_path)
    if path.is_absolute() and path.exists() and path.suffix == ".json":
        return _load_world_from_file(path)

    name = name_or_path.replace(".json", "")
    candidate = _WORLDS_DIR / f"{name}.json"
    if candidate.exists():
        return _load_world_from_file(candidate)

    for f in _WORLDS_DIR.glob("*.json"):
        if f.stem == name:
            return _load_world_from_file(f)

    return None


def _load_world_from_file(path: Path) -> CampaignBackground:
    data = _read_json(path)
    return CampaignBackground(
        raw_input=data.get("raw_input", ""),
        world_setting=data.get("world_setting", ""),
        factions=data.get("factions", []),
        history=data.get("history", []),
        important_locations=data.get("important_locations", []),
        initial_situation=data.get("initial_situation", ""),
        power_system=data.get("power_system", ""),
    )


def list_worlds() -> list[str]:
    if not _WORLDS_DIR.exists():
        return []
    return sorted(
        f.stem for f in _WORLDS_DIR.glob("*.json")
    )
