from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ActionUnit:
    character_id: Optional[str] = None
    dialogue: Optional[str] = None
    action: Optional[str] = None
    inner_thought: Optional[str] = None
    audience: Optional[list[str]] = None
    entered: Optional[list[str]] = None
    left: Optional[list[str]] = None


@dataclass
class JudgmentResult:
    next_speaker: str
    reason: str
    force_environment: bool = False
    corrected_present_characters: Optional[list[str]] = None


@dataclass
class CharacterProfile:
    id: str
    name: str
    character_type: str = "npc"
    personality: str = ""
    background: str = ""
    appearance: str = ""
    skills: dict[str, int] = field(default_factory=dict)
    attributes: dict[str, int] = field(default_factory=dict)
    relationships: dict[str, str] = field(default_factory=dict)
    notes: str = ""
    physique: dict = field(default_factory=dict)
    identity: dict = field(default_factory=dict)
    clothing: str = ""
    behavior: dict = field(default_factory=dict)
    intimate_features: str = ""


@dataclass
class CharacterContext:
    character_id: str
    action_units: list[ActionUnit] = field(default_factory=list)


@dataclass
class EnvironmentEntry:
    id: str
    description: str
    visible_to: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class DialogueEntry:
    character_id: str
    dialogue: str
    timestamp: str = ""


@dataclass
class CheckpointSummary:
    id: str
    timestamp: str
    stage_label: str
    summary: str
    character_updates: dict[str, dict] = field(default_factory=dict)
    environment_state: str = ""


@dataclass
class SceneState:
    present_characters: list[str] = field(default_factory=list)
    action_count_since_env: int = 0
    total_action_count: int = 0


@dataclass
class DiceRollResult:
    expression: str
    rolls: list[int]
    modifier: int
    total: int


@dataclass
class CheckResult:
    success: bool
    critical: bool
    fumble: bool
    roll: DiceRollResult
    skill_value: int
    difficulty: Optional[int] = None
    result_description: str = ""


@dataclass
class RulesConfig:
    system_name: str
    description: str = ""
    primary_dice: str = "d100"
    attributes: dict[str, str] = field(default_factory=dict)
    skills: dict[str, dict] = field(default_factory=dict)


@dataclass
class CampaignBackground:
    raw_input: str
    world_setting: str = ""
    factions: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    important_locations: list[dict] = field(default_factory=list)
    initial_situation: str = ""
    power_system: str = ""


@dataclass
class GameSession:
    id: str
    name: str
    mode: str = "player-present"
    mechanics_mode: str = "pure-narrative"
    campaign_background: Optional[CampaignBackground] = None
    characters: dict[str, CharacterProfile] = field(default_factory=dict)
    character_contexts: dict[str, CharacterContext] = field(default_factory=dict)
    environment_entries: list[EnvironmentEntry] = field(default_factory=list)
    dialogue_log: list[DialogueEntry] = field(default_factory=list)
    scene_state: SceneState = field(default_factory=SceneState)
    checkpoints: list[CheckpointSummary] = field(default_factory=list)
    rules_config: Optional[RulesConfig] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AgentDirective:
    content: str
    timestamp: str = ""
