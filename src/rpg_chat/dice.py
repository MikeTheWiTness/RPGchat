import re
import random

from rpg_chat.types import DiceRollResult, CheckResult, RulesConfig


class DiceEngine:
    def __init__(self):
        self._rng = random.Random()

    def roll(self, expression: str) -> DiceRollResult:
        match = re.match(r'^(\d*)d(\d+)([+-]\d+)?$', expression)
        if not match:
            raise ValueError(f"无效的骰子表达式: {expression}")

        count = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        modifier_str = match.group(3)
        modifier = int(modifier_str) if modifier_str else 0

        if count < 1 or sides < 2:
            raise ValueError(f"无效的骰子表达式: {expression}")

        rolls = [self._rng.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier

        return DiceRollResult(
            expression=expression,
            rolls=rolls,
            modifier=modifier,
            total=total,
        )

    def check(
        self,
        skill_name: str,
        character_skill_value: int,
        rules: RulesConfig,
        difficulty: int | None = None,
    ) -> CheckResult:
        if rules.primary_dice == "d20":
            result = self.roll(f"1d20")
            adjusted = result.total
            critical = adjusted == 20
            fumble = adjusted == 1
            if difficulty is not None:
                success = adjusted >= difficulty
            else:
                success = adjusted >= character_skill_value
        else:
            result = self.roll(rules.primary_dice)
            adjusted = result.total
            sides = int(rules.primary_dice.lstrip("d"))
            critical = adjusted == 1
            fumble = adjusted == sides
            success = adjusted <= character_skill_value

        return CheckResult(
            success=success,
            critical=critical,
            fumble=fumble,
            roll=result,
            skill_value=character_skill_value,
            difficulty=difficulty,
            result_description="",
        )


DICE_PATTERN = re.compile(r'^(\d*)d(\d+)([+-]\d+)?$')
