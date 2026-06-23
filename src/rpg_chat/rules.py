from rpg_chat.types import RulesConfig, CheckResult
from rpg_chat.dice import DiceEngine

COC_7TH = RulesConfig(
    system_name="CoC 7th",
    description="克苏鲁的呼唤第7版",
    primary_dice="d100",
    attributes={
        "STR": "力量", "CON": "体质", "DEX": "敏捷",
        "APP": "外貌", "POW": "意志", "SIZ": "体型",
        "INT": "智力", "EDU": "教育",
    },
    skills={
        "侦查": {"base": 25}, "图书馆使用": {"base": 20},
        "聆听": {"base": 20}, "潜行": {"base": 20},
        "心理学": {"base": 10}, "格斗": {"base": 25},
        "射击": {"base": 20}, "急救": {"base": 30},
        "历史": {"base": 5}, "神秘学": {"base": 5},
        "说服": {"base": 10}, "话术": {"base": 5},
        "攀爬": {"base": 20}, "游泳": {"base": 20},
        "驾驶": {"base": 20}, "电气维修": {"base": 10},
    },
)

DND_5E = RulesConfig(
    system_name="D&D 5e",
    description="龙与地下城第5版",
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
    "coc": COC_7TH,
    "dnd": DND_5E,
}


class SkillCheckHandler:
    def __init__(self, dice_engine: DiceEngine | None = None):
        self._dice = dice_engine or DiceEngine()

    def handle_directive(
        self, directive_content: str, rules: RulesConfig | None,
        character_skills: dict[str, int]
    ) -> CheckResult | None:
        if not directive_content.startswith("检定 "):
            return None

        skill_name = directive_content[3:].strip()
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

        skill_value = character_skills.get(skill_name, 0)

        if rules.primary_dice == "d100":
            skill_value = character_skills.get(skill_name, 1)
        else:
            skill_value = character_skills.get(skill_name, 0)

        result = self._dice.check(skill_name, skill_value, rules)

        if rules.primary_dice == "d100":
            desc = (
                f"d100={result.roll.total} vs {skill_name}"
                f"{skill_value} → "
                f"{'成功' if result.success else '失败'}"
            )
            if result.critical:
                desc += " (大成功!)"
            elif result.fumble:
                desc += " (大失败!)"
        else:
            desc = (
                f"d20={result.roll.total} vs DC{rules.primary_dice} "
                f"{skill_name}+{skill_value} → "
                f"{'成功' if result.success else '失败'}"
            )
            if result.critical:
                desc += " (暴击!)"

        return CheckResult(
            success=result.success,
            critical=result.critical,
            fumble=result.fumble,
            roll=result.roll,
            skill_value=skill_value,
            result_description=desc,
        )
