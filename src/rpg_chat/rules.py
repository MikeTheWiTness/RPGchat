from rpg_chat.types import RulesConfig, CheckResult
from rpg_chat.dice import DiceEngine

D20_STANDARD = RulesConfig(
    system_name="D20 Standard",
    description="标准 d20 系统",
    primary_dice="d20",
    attributes={
        "STR": "力量", "DEX": "敏捷", "CON": "体质",
        "INT": "智力", "WIS": "感知", "CHA": "魅力",
    },
    skills={
        "运动": {"attribute": "STR"},
        "特技": {"attribute": "DEX"},
        "巧手": {"attribute": "DEX"},
        "隐匿": {"attribute": "DEX"},
        "奥秘": {"attribute": "INT"},
        "历史": {"attribute": "INT"},
        "调查": {"attribute": "INT"},
        "自然": {"attribute": "INT"},
        "宗教": {"attribute": "INT"},
        "驯兽": {"attribute": "WIS"},
        "洞悉": {"attribute": "WIS"},
        "医药": {"attribute": "WIS"},
        "察觉": {"attribute": "WIS"},
        "生存": {"attribute": "WIS"},
        "欺瞒": {"attribute": "CHA"},
        "威吓": {"attribute": "CHA"},
        "表演": {"attribute": "CHA"},
        "游说": {"attribute": "CHA"},
    },
)

PRESETS = {
    "d20": D20_STANDARD,
}

DEFAULT_DC = 10


class SkillCheckHandler:
    def __init__(self, dice_engine: DiceEngine | None = None):
        self._dice = dice_engine or DiceEngine()

    def handle_directive(
        self, directive_content: str, rules: RulesConfig | None,
        character_skills: dict[str, int]
    ) -> CheckResult | None:
        if not directive_content.startswith("检定 "):
            return None

        rest = directive_content[3:].strip()
        if not rest:
            return None

        parts = rest.split()
        skill_name = parts[0]
        if not skill_name:
            return None

        if rules is None:
            return CheckResult(
                success=False,
                critical=False,
                fumble=False,
                roll=None,
                skill_value=0,
                result_description="纯叙事模式不支持检定",
            )

        dc = DEFAULT_DC
        if len(parts) >= 2:
            try:
                dc = int(parts[1])
            except ValueError:
                dc = DEFAULT_DC

        skill_value = character_skills.get(skill_name, 0)

        result = self._dice.check_skill(skill_modifier=skill_value, dc=dc)

        desc = (
            f"d20={result.roll.rolls[0]} vs DC{dc} "
            f"{skill_name}+{skill_value} "
            f"→ {'成功' if result.success else '失败'}"
        )
        if result.critical:
            desc += " (暴击!)"
        elif result.fumble:
            desc += " (大失败!)"

        return CheckResult(
            success=result.success,
            critical=result.critical,
            fumble=result.fumble,
            roll=result.roll,
            skill_value=skill_value,
            difficulty=dc,
            result_description=desc,
        )
