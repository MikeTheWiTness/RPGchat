import random
import pytest
from rpg_chat.dice import DiceEngine, DiceRollResult, CheckResult


class TestD20System:
    @pytest.fixture
    def engine(self):
        return DiceEngine(seed=42)

    def test_roll_d20_returns_d20_result(self, engine):
        result = engine.roll_d20()
        assert isinstance(result, DiceRollResult)
        assert 1 <= result.rolls[0] <= 20
        assert len(result.rolls) == 1
        assert result.modifier == 0
        assert result.total == result.rolls[0]

    def test_roll_d20_with_positive_modifier(self, engine):
        result = engine.roll_d20(modifier=5)
        assert result.modifier == 5
        assert result.total == result.rolls[0] + 5

    def test_roll_d20_with_negative_modifier(self, engine):
        result = engine.roll_d20(modifier=-3)
        assert result.modifier == -3
        assert result.total == result.rolls[0] - 3

    def test_roll_d20_is_deterministic_with_seed(self):
        engine1 = DiceEngine(seed=123)
        engine2 = DiceEngine(seed=123)
        for _ in range(10):
            assert engine1.roll_d20().total == engine2.roll_d20().total

    def test_check_skill_success_when_roll_plus_mod_ge_dc(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 15
        result = engine.check_skill(skill_modifier=3, dc=15)
        assert result.success is True
        assert result.critical is False
        assert result.fumble is False

    def test_check_skill_failure_when_roll_plus_mod_lt_dc(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 10
        result = engine.check_skill(skill_modifier=3, dc=15)
        assert result.success is False
        assert result.critical is False
        assert result.fumble is False

    def test_check_skill_critical_on_nat20(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 20
        result = engine.check_skill(skill_modifier=0, dc=30)
        assert result.critical is True
        assert result.success is True

    def test_check_skill_fumble_on_nat1(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 1
        result = engine.check_skill(skill_modifier=20, dc=5)
        assert result.fumble is True
        assert result.success is False

    def test_check_skill_boundary_dc_equals_total(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 12
        result = engine.check_skill(skill_modifier=3, dc=15)
        assert result.success is True

    def test_check_skill_returns_check_result(self, engine):
        result = engine.check_skill(skill_modifier=5, dc=12)
        assert isinstance(result, CheckResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.critical, bool)
        assert isinstance(result.fumble, bool)
        assert result.skill_value == 5
        assert result.difficulty == 12
        assert result.roll is not None

    def test_critical_always_succeeds_even_if_below_dc(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 20
        result = engine.check_skill(skill_modifier=0, dc=100)
        assert result.success is True
        assert result.critical is True

    def test_fumble_always_fails_even_if_above_dc(self):
        engine = DiceEngine()
        engine._rng = random.Random()
        engine._rng.randint = lambda a, b: 1
        result = engine.check_skill(skill_modifier=50, dc=1)
        assert result.success is False
        assert result.fumble is True
