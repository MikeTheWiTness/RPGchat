import math
import random

from rpg_chat.types import ActionUnit, JudgmentResult
from rpg_chat.llm import LLMGateway
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler


class JudgmentEngine:
    def __init__(
        self,
        llm: LLMGateway,
        context_assembler: ContextAssembler,
        scene_tracker: SceneTracker,
        max_consecutive_characters: int = 5,
        sanity_check_interval: int = 10,
        env_force_lambda: float = 0.15,
    ):
        self._llm = llm
        self._context_assembler = context_assembler
        self._scene_tracker = scene_tracker
        self.max_consecutive_characters = max_consecutive_characters
        self.sanity_check_interval = sanity_check_interval
        # 泊松式递增概率：p = 1 - exp(-lambda * count)
        # lambda=0.15 时：count=5 → p≈0.53，count=10 → p≈0.78，count=15 → p≈0.89
        self.env_force_lambda = env_force_lambda

    def _force_env_probability(self, count: int) -> float:
        """返回本轮强制环境的概率。count=0 时为 0，随 count 递增趋近 1。"""
        if count <= 0:
            return 0.0
        return 1.0 - math.exp(-self.env_force_lambda * count)

    def _roll_force_env(self) -> bool:
        count = self._scene_tracker.action_count_since_env
        p = self._force_env_probability(count)
        return random.random() < p

    def judge(self) -> JudgmentResult:
        action_count = self._scene_tracker.action_count_since_env
        total_count = self._scene_tracker.total_action_count

        force_env = self._roll_force_env()
        # 环境最多连续 4 轮，再连就强制切角色（防死循环）
        force_character = self._scene_tracker.consecutive_env_count >= 4

        sanity_check = (total_count > 0 and
                        total_count % self.sanity_check_interval == 0)

        context = self._context_assembler.assemble_for_judgment()
        result = self._llm.generate_judgment(
            context, force_env_check=force_env, sanity_check=sanity_check
        )

        judgment = JudgmentResult(
            next_speaker=result["next_speaker"],
            reason=result["reason"],
            force_environment=result.get("force_environment", force_env),
            corrected_present_characters=result.get(
                "corrected_present_characters"
            ),
        )

        if force_env:
            judgment.next_speaker = "environment"
            judgment.force_environment = True
            if not judgment.reason:
                judgment.reason = (
                    f"已连续 {action_count} 轮角色发言，按递增概率触发环境轮"
                )

        # 环境连太久了，强制切回角色
        if force_character:
            judgment.next_speaker = result.get("next_speaker", "")
            if not judgment.next_speaker or judgment.next_speaker == "environment":
                present = self._scene_tracker.get_present()
                judgment.next_speaker = present[0] if present else "environment"
            judgment.force_environment = False
            judgment.reason = (
                f"已连续 {self._scene_tracker.consecutive_env_count} 轮环境，"
                f"强制切回角色 {judgment.next_speaker}"
            )

        if sanity_check and judgment.corrected_present_characters is not None:
            self._scene_tracker.apply_correction(
                judgment.corrected_present_characters
            )

        return judgment

    def generate_environment(self, gm_hint: str = "") -> ActionUnit:
        context = self._context_assembler.assemble_for_judgment()
        if gm_hint:
            context["gm_hint"] = gm_hint
        return self._llm.generate_environment_action_unit(context)
