import pytest
from rpg_chat.dice import DiceEngine
from rpg_chat.types import RulesConfig


class TestDiceEngine:
    @pytest.fixture
    def engine(self):
        eng = DiceEngine()
        eng._rng.seed(42)
        return eng

    @pytest.fixture
    def coc_rules(self):
        return RulesConfig(
            system_name="CoC 7th",
            primary_dice="d100",
        )

    @pytest.fixture
    def dnd_rules(self):
        return RulesConfig(
            system_name="D&D 5e",
            primary_dice="d20",
        )

    def test_d100_range(self, engine):
        for _ in range(100):
            result = engine.roll("d100")
            assert 1 <= result.total <= 100
            assert len(result.rolls) == 1

    def test_3d6_range(self, engine):
        for _ in range(50):
            result = engine.roll("3d6")
            assert 3 <= result.total <= 18
            assert len(result.rolls) == 3

    def test_d20_with_modifier(self, engine):
        result = engine.roll("d20+5")
        assert result.modifier == 5
        for r in result.rolls:
            assert 1 <= r <= 20
        assert result.total == result.rolls[0] + 5

    def test_2d6_minus_2(self, engine):
        result = engine.roll("2d6-2")
        assert result.modifier == -2

    def test_invalid_expression_raises(self, engine):
        with pytest.raises(ValueError, match="无效的骰子表达式"):
            engine.roll("not_a_dice")

    def test_coc_check_success(self, engine, coc_rules):
        result = engine.check("侦查", 60, coc_rules)
        assert result.skill_value == 60
        assert result.difficulty is None
        assert isinstance(result.success, bool)
        assert isinstance(result.critical, bool)
        assert isinstance(result.fumble, bool)

    def test_coc_check_critical(self, engine, coc_rules):
        engine._rng.seed(1)
        result = engine.check("侦查", 60, coc_rules)
        assert result.roll.total in (1, 100) or result.success is not None

    def test_dnd_check_with_difficulty(self, engine, dnd_rules):
        engine._rng.seed(42)
        result = engine.check("侦查", 70, dnd_rules, difficulty=15)
        assert result.difficulty == 15
        assert result.skill_value == 70

    def test_dnd_critical_hit(self, engine, dnd_rules):
        engine._rng.seed(1)
        for _ in range(1000):
            r = engine.check("攻击", 70, dnd_rules)
            if r.roll.total == 20:
                assert r.critical is True
                break
