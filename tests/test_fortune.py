import random
import pytest
from rpg_chat.fortune import FortuneSystem, FortuneLevel


class TestFortuneSystem:
    @pytest.fixture
    def system(self):
        return FortuneSystem(seed=42)

    def test_fortune_level_has_five_levels(self):
        assert FortuneLevel.GREAT_OMINOUS == "great_ominous"
        assert FortuneLevel.OMINOUS == "ominous"
        assert FortuneLevel.NORMAL == "normal"
        assert FortuneLevel.AUSPICIOUS == "auspicious"
        assert FortuneLevel.GREAT_AUSPICIOUS == "great_auspicious"

    def test_roll_fortune_returns_valid_level(self, system):
        for _ in range(100):
            level = system.roll_fortune()
            assert level in [
                FortuneLevel.GREAT_OMINOUS,
                FortuneLevel.OMINOUS,
                FortuneLevel.NORMAL,
                FortuneLevel.AUSPICIOUS,
                FortuneLevel.GREAT_AUSPICIOUS,
            ]

    def test_boundary_values(self):
        system = FortuneSystem()
        for i in range(1, 6):
            system._rng = random.Random()
            system._rng.randint = lambda a, b: i
            assert system.roll_fortune() == FortuneLevel.GREAT_OMINOUS, f"roll={i}"

        for i in range(6, 26):
            system._rng = random.Random()
            system._rng.randint = lambda a, b: i
            assert system.roll_fortune() == FortuneLevel.OMINOUS, f"roll={i}"

        for i in range(26, 75):
            system._rng = random.Random()
            system._rng.randint = lambda a, b: i
            assert system.roll_fortune() == FortuneLevel.NORMAL, f"roll={i}"

        for i in range(75, 95):
            system._rng = random.Random()
            system._rng.randint = lambda a, b: i
            assert system.roll_fortune() == FortuneLevel.AUSPICIOUS, f"roll={i}"

        for i in range(95, 101):
            system._rng = random.Random()
            system._rng.randint = lambda a, b: i
            assert system.roll_fortune() == FortuneLevel.GREAT_AUSPICIOUS, f"roll={i}"

    def test_fortune_prompt_returns_text_for_each_level(self, system):
        for level in FortuneLevel:
            prompt = system.fortune_prompt(level)
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_probability_distribution(self):
        system = FortuneSystem(seed=12345)
        total = 10000
        counts = {
            FortuneLevel.GREAT_OMINOUS: 0,
            FortuneLevel.OMINOUS: 0,
            FortuneLevel.NORMAL: 0,
            FortuneLevel.AUSPICIOUS: 0,
            FortuneLevel.GREAT_AUSPICIOUS: 0,
        }
        for _ in range(total):
            level = system.roll_fortune()
            counts[level] += 1

        assert 0.03 <= counts[FortuneLevel.GREAT_OMINOUS] / total <= 0.07
        assert 0.15 <= counts[FortuneLevel.OMINOUS] / total <= 0.25
        assert 0.44 <= counts[FortuneLevel.NORMAL] / total <= 0.54
        assert 0.15 <= counts[FortuneLevel.AUSPICIOUS] / total <= 0.25
        assert 0.03 <= counts[FortuneLevel.GREAT_AUSPICIOUS] / total <= 0.07
