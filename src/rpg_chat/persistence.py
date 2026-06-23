import json
import os
from datetime import datetime, timezone
from pathlib import Path

from rpg_chat.types import GameSession


def _default_serializer(obj):
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = _default_serializer(value)
        return result
    if isinstance(obj, list):
        return [_default_serializer(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _default_serializer(v) for k, v in obj.items()}
    return obj


def save(session: GameSession, filepath: str | None = None):
    if filepath is None:
        save_dir = Path("./saves")
        save_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(save_dir / f"{session.name}.json")

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    session.updated_at = datetime.now(timezone.utc).isoformat()

    data = _default_serializer(session)

    if path.exists():
        backup_path = path.with_suffix(".json.bak")
        path.replace(backup_path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _deserialize_session(data: dict) -> GameSession:
    from rpg_chat.types import (
        ActionUnit,
        AgentDirective,
        CampaignBackground,
        CharacterContext,
        CharacterProfile,
        CheckpointSummary,
        DialogueEntry,
        EnvironmentEntry,
        SceneState,
        RulesConfig,
        DiceRollResult,
        CheckResult,
    )

    def _make_au(d):
        return ActionUnit(
            character_id=d.get("character_id"),
            dialogue=d.get("dialogue"),
            action=d.get("action"),
            inner_thought=d.get("inner_thought"),
            audience=d.get("audience"),
            entered=d.get("entered"),
            left=d.get("left"),
        )

    def _make_profile(d):
        return CharacterProfile(
            id=d.get("id", ""),
            name=d.get("name", ""),
            character_type=d.get("character_type", "npc"),
            personality=d.get("personality", ""),
            background=d.get("background", ""),
            appearance=d.get("appearance", ""),
            skills=d.get("skills", {}),
            attributes=d.get("attributes", {}),
            relationships=d.get("relationships", {}),
            notes=d.get("notes", ""),
            physique=d.get("physique", {}),
            identity=d.get("identity", {}),
            clothing=d.get("clothing", ""),
            behavior=d.get("behavior", {}),
            intimate_features=d.get("intimate_features", ""),
        )

    def _make_ctx(d):
        return CharacterContext(
            character_id=d.get("character_id", ""),
            action_units=[_make_au(au) for au in d.get("action_units", [])],
        )

    def _make_env_entry(d):
        return EnvironmentEntry(
            id=d.get("id", ""),
            description=d.get("description", ""),
            visible_to=d.get("visible_to", []),
            created_at=d.get("created_at", ""),
        )

    def _make_dialogue_entry(d):
        return DialogueEntry(
            character_id=d.get("character_id", ""),
            dialogue=d.get("dialogue", ""),
            timestamp=d.get("timestamp", ""),
        )

    def _make_checkpoint(d):
        return CheckpointSummary(
            id=d.get("id", ""),
            timestamp=d.get("timestamp", ""),
            stage_label=d.get("stage_label", ""),
            summary=d.get("summary", ""),
            character_updates=d.get("character_updates", {}),
            environment_state=d.get("environment_state", ""),
        )

    def _make_rules(d):
        if d is None:
            return None
        return RulesConfig(
            system_name=d.get("system_name", ""),
            description=d.get("description", ""),
            primary_dice=d.get("primary_dice", "d100"),
            attributes=d.get("attributes", {}),
            skills=d.get("skills", {}),
        )

    def _make_campaign(d):
        if d is None:
            return None
        return CampaignBackground(
            raw_input=d.get("raw_input", ""),
            world_setting=d.get("world_setting", ""),
            factions=d.get("factions", []),
            history=d.get("history", []),
            important_locations=d.get("important_locations", []),
            initial_situation=d.get("initial_situation", ""),
        )

    def _make_scene(d):
        return SceneState(
            present_characters=d.get("present_characters", []),
            action_count_since_env=d.get("action_count_since_env", 0),
            total_action_count=d.get("total_action_count", 0),
        )

    return GameSession(
        id=data.get("id", ""),
        name=data.get("name", ""),
        mode=data.get("mode", "player-present"),
        mechanics_mode=data.get("mechanics_mode", "pure-narrative"),
        campaign_background=_make_campaign(data.get("campaign_background")),
        characters={
            k: _make_profile(v)
            for k, v in data.get("characters", {}).items()
        },
        character_contexts={
            k: _make_ctx(v)
            for k, v in data.get("character_contexts", {}).items()
        },
        environment_entries=[
            _make_env_entry(e) for e in data.get("environment_entries", [])
        ],
        dialogue_log=[
            _make_dialogue_entry(e) for e in data.get("dialogue_log", [])
        ],
        scene_state=_make_scene(data.get("scene_state", {})),
        checkpoints=[
            _make_checkpoint(c) for c in data.get("checkpoints", [])
        ],
        rules_config=_make_rules(data.get("rules_config")),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


def load(filepath: str) -> GameSession:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"存档文件不存在: {filepath}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"存档文件已损坏，JSON 解析失败: {e}")

    if not isinstance(data, dict):
        raise ValueError("存档文件格式不正确")

    if "id" not in data or "name" not in data:
        raise ValueError("存档文件缺少必要字段")

    return _deserialize_session(data)


def list_saves(save_dir: str = "./saves") -> list[str]:
    path = Path(save_dir)
    if not path.exists():
        return []
    return sorted(
        str(p) for p in path.glob("*.json") if not p.name.endswith(".json.bak")
    )


def delete_save(filepath: str):
    path = Path(filepath)
    path.unlink(missing_ok=True)
    backup = path.with_suffix(".json.bak")
    backup.unlink(missing_ok=True)
