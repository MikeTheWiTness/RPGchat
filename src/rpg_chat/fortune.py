import random
from enum import Enum


class FortuneLevel(str, Enum):
    GREAT_OMINOUS = "great_ominous"
    OMINOUS = "ominous"
    NORMAL = "normal"
    AUSPICIOUS = "auspicious"
    GREAT_AUSPICIOUS = "great_auspicious"


class FortuneSystem:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def roll_fortune(self) -> FortuneLevel:
        roll = self._rng.randint(1, 100)
        if roll <= 5:
            return FortuneLevel.GREAT_OMINOUS
        elif roll <= 25:
            return FortuneLevel.OMINOUS
        elif roll <= 74:
            return FortuneLevel.NORMAL
        elif roll <= 94:
            return FortuneLevel.AUSPICIOUS
        else:
            return FortuneLevel.GREAT_AUSPICIOUS

    def fortune_prompt(self, level: FortuneLevel) -> str:
        prompts = {
            FortuneLevel.GREAT_OMINOUS: "当前运势：大凶。角色状态极差，容易犯严重错误，事情往往朝最坏的方向发展，出现意外的失误或出糗。",
            FortuneLevel.OMINOUS: "当前运势：凶。角色状态不佳，容易出小差错，事情进展不太顺利，表现偏消极。",
            FortuneLevel.NORMAL: "当前运势：平。正常状态，按角色平时的水平发挥即可。",
            FortuneLevel.AUSPICIOUS: "当前运势：吉。角色状态不错，事情进展比较顺利，有小的成功或好运。",
            FortuneLevel.GREAT_AUSPICIOUS: "当前运势：大吉。角色超常发挥，灵感爆发，事情意外地顺利，有出人意料的好结果。",
        }
        return prompts[level]
