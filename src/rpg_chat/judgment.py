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
    ):
        self._llm = llm
        self._context_assembler = context_assembler
        self._scene_tracker = scene_tracker
        self.max_consecutive_characters = max_consecutive_characters
        self.sanity_check_interval = sanity_check_interval

    def judge(self) -> JudgmentResult:
        action_count = self._scene_tracker.action_count_since_env
        total_count = self._scene_tracker.total_action_count

        force_env = action_count >= self.max_consecutive_characters
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

        if sanity_check and judgment.corrected_present_characters is not None:
            self._scene_tracker.apply_correction(
                judgment.corrected_present_characters
            )

        return judgment

    def generate_environment(self) -> ActionUnit:
        context = self._context_assembler.assemble_for_judgment()
        return self._llm.generate_environment_action_unit(context)
