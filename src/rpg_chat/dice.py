import random

from rpg_chat.types import DiceRollResult, CheckResult


class DiceEngine:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def roll_d20(self, modifier: int = 0) -> DiceRollResult:
        roll = self._rng.randint(1, 20)
        total = roll + modifier
        expression = f"1d20"
        if modifier > 0:
            expression += f"+{modifier}"
        elif modifier < 0:
            expression += f"{modifier}"

        return DiceRollResult(
            expression=expression,
            rolls=[roll],
            modifier=modifier,
            total=total,
        )

    def check_skill(self, skill_modifier: int, dc: int) -> CheckResult:
        roll_result = self.roll_d20()
        roll = roll_result.rolls[0]
        total = roll + skill_modifier

        critical = roll == 20
        fumble = roll == 1

        if critical:
            success = True
        elif fumble:
            success = False
        else:
            success = total >= dc

        return CheckResult(
            success=success,
            critical=critical,
            fumble=fumble,
            roll=roll_result,
            skill_value=skill_modifier,
            difficulty=dc,
            result_description="",
        )
