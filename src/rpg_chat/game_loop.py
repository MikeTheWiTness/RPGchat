from dataclasses import dataclass, field
from typing import Optional

from rpg_chat.types import (
    ActionUnit, AgentDirective, CampaignBackground, CharacterProfile,
    GameSession, JudgmentResult, RulesConfig, CheckResult,
)
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.parser import parse_pc_input
from rpg_chat.llm import LLMGateway
from rpg_chat.judgment import JudgmentEngine
from rpg_chat.rules import SkillCheckHandler, PRESETS
from rpg_chat.campaign import CampaignBackgroundParser
from rpg_chat.checkpoint import CheckpointManager
from rpg_chat.persistence import save as persist_save, load as persist_load
from rpg_chat.preset_loader import (
    load_character as preset_load_character,
    list_characters as preset_list_characters,
    load_world as preset_load_world,
    list_worlds as preset_list_worlds,
)


@dataclass
class StepResult:
    action_unit: Optional[ActionUnit] = None
    judgment: Optional[JudgmentResult] = None
    directive: Optional[AgentDirective] = None
    check_result: Optional[CheckResult] = None
    system_message: str = ""


@dataclass
class GameLoopConfig:
    max_consecutive_characters: int = 5
    sanity_check_interval: int = 10
    mechanics_mode: str = "pure-narrative"
    rules_system: str = ""
    auto_chain_enabled: bool = True
    auto_chain_max: int = 3


class GameLoop:
    def __init__(
        self,
        llm_gateway: LLMGateway,
        character_store: CharacterStore,
        dialogue_log: DialogueLog,
        environment_store: EnvironmentStore,
        scene_tracker: SceneTracker,
        context_assembler: ContextAssembler,
        config: GameLoopConfig | None = None,
    ):
        self._llm = llm_gateway
        self._characters = character_store
        self._dialogue_log = dialogue_log
        self._environment = environment_store
        self._scene = scene_tracker
        self._context = context_assembler
        self._config = config or GameLoopConfig()

        self._judgment_engine = JudgmentEngine(
            llm=llm_gateway,
            context_assembler=context_assembler,
            scene_tracker=scene_tracker,
            max_consecutive_characters=self._config.max_consecutive_characters,
            sanity_check_interval=self._config.sanity_check_interval,
        )
        self._campaign_parser = CampaignBackgroundParser(llm_gateway)
        self._skill_handler = SkillCheckHandler()
        self._checkpoint_manager = CheckpointManager(
            llm=llm_gateway,
            character_store=character_store,
            dialogue_log=dialogue_log,
            environment_store=environment_store,
        )

        self._session: Optional[GameSession] = None
        self._pc_id: Optional[str] = None
        self._rules: Optional[RulesConfig] = None
        self._last_judgment: Optional[JudgmentResult] = None
        self._running = False
        self._auto_mode = False

    @property
    def session(self) -> Optional[GameSession]:
        return self._session

    @property
    def present_characters(self) -> list[str]:
        return self._scene.get_present()

    @property
    def last_judgment(self) -> Optional[JudgmentResult]:
        return self._last_judgment

    def new_game(
        self,
        name: str,
        campaign_input: str,
        pc_profile: CharacterProfile,
        mechanics_mode: str = "pure-narrative",
        rules_system: str = "",
    ) -> str:
        background = self._campaign_parser.parse(campaign_input)

        rules = None
        if mechanics_mode == "light-rules" and rules_system:
            rules = PRESETS.get(rules_system)

        session = GameSession(
            id=f"session_{name}",
            name=name,
            mode="player-present",
            mechanics_mode=mechanics_mode,
            campaign_background=background,
            rules_config=rules,
        )

        self._characters.create_character(pc_profile)
        session.characters[pc_profile.id] = pc_profile
        self._pc_id = pc_profile.id

        self._session = session
        self._rules = rules
        self._running = True

        self._context.set_campaign_background(background)

        env_au = self._judgment_engine.generate_environment()
        self._process_action_unit(env_au)

        self._last_judgment = self._judgment_engine.judge()

        result_text = self._format_action_unit(env_au)
        present_text = self._format_present()
        next_text = (
            f"[判断] 下一个发言: {self._last_judgment.next_speaker} "
            f"({self._last_judgment.reason})"
        )
        return f"{result_text}\n{present_text}\n{next_text}"

    def handle_input(self, user_input: str) -> str:
        if not self._running:
            return "游戏未运行"

        user_input = user_input.strip()

        if user_input == "{继续}":
            result = self._handle_continue()
            result += self._auto_chain()
            return result

        if user_input == "{保存}":
            return self._handle_save()

        if user_input == "{查看在场}":
            return self._format_present()

        if user_input.startswith("{检定 "):
            return self._handle_skill_check(user_input)

        if user_input.startswith("{创建NPC "):
            return self._handle_create_npc(user_input)

        if user_input.startswith("{导入角色 "):
            return self._handle_import_character(user_input)

        if user_input == "{列出角色预设}":
            return self._handle_list_character_presets()

        if user_input.startswith("{导入世界观 "):
            return self._handle_import_world(user_input)

        if user_input == "{列出世界观预设}":
            return self._handle_list_world_presets()

        result = self._handle_pc_input(user_input)
        result += self._auto_chain()
        return result

    def _handle_continue(self) -> str:
        if self._last_judgment.force_environment:
            next_speaker = "environment"
        else:
            next_speaker = self._last_judgment.next_speaker

        if next_speaker == "environment":
            au = self._judgment_engine.generate_environment()
        elif next_speaker == self._pc_id:
            return "[系统] 轮到 PC 发言，请输入角色动作。"
        else:
            profile = self._characters.get_profile(next_speaker)
            if profile is None:
                profile = self._characters.create_npc_on_the_fly(
                    next_speaker, "未知角色"
                )
                if self._session:
                    self._session.characters[profile.id] = profile
            ctx = self._context.assemble_for_character(next_speaker)
            au = self._llm.generate_npc_action_unit(ctx)

        self._process_action_unit(au)
        self._last_judgment = self._judgment_engine.judge()

        output = self._format_action_unit(au)
        output += f"\n[判断] → {self._last_judgment.next_speaker}"
        if self._last_judgment.corrected_present_characters:
            output += (
                f"\n[校验] 在场人员已修正: "
                f"{', '.join(self._last_judgment.corrected_present_characters)}"
            )
        return output

    def _auto_chain(self) -> str:
        if not self._config.auto_chain_enabled:
            return ""
        output_parts = []
        for _ in range(self._config.auto_chain_max):
            if self._last_judgment is None:
                break
            next_speaker = self._last_judgment.next_speaker
            if self._last_judgment.force_environment:
                next_speaker = "environment"
            if next_speaker == self._pc_id:
                break
            step = self._generate_step(next_speaker)
            output_parts.append(step)
        return "\n" + "\n".join(output_parts) if output_parts else ""

    def _generate_step(self, speaker_id: str) -> str:
        if speaker_id == "environment":
            au = self._judgment_engine.generate_environment()
        else:
            profile = self._characters.get_profile(speaker_id)
            if profile is None:
                profile = self._characters.create_npc_on_the_fly(
                    speaker_id, "未知角色"
                )
                if self._session:
                    self._session.characters[profile.id] = profile
            ctx = self._context.assemble_for_character(speaker_id)
            au = self._llm.generate_npc_action_unit(ctx)

        self._process_action_unit(au)
        self._last_judgment = self._judgment_engine.judge()

        output = self._format_action_unit(au)
        output += f"\n[判断] → {self._last_judgment.next_speaker}"
        if self._last_judgment.corrected_present_characters:
            output += (
                f"\n[校验] 在场人员已修正: "
                f"{', '.join(self._last_judgment.corrected_present_characters)}"
            )
        return output

    def _handle_create_npc(self, directive: str) -> str:
        inner = directive[1:-1]
        parts = inner.split(" ", 2)
        if len(parts) < 3:
            return "[系统] 用法: {创建NPC 英文id 角色名称和描述}"
        npc_id = parts[1]
        description = parts[2]

        if self._characters.get_profile(npc_id) is not None:
            return f"[系统] NPC '{npc_id}' 已存在"

        campaign_ctx = {}
        if self._session and self._session.campaign_background:
            cb = self._session.campaign_background
            campaign_ctx = {
                "world_setting": cb.world_setting,
                "initial_situation": cb.initial_situation,
            }

        profile = self._llm.create_npc_profile(npc_id, description, campaign_ctx)
        self._characters.create_character(profile)
        if self._session:
            self._session.characters[profile.id] = profile

        return (
            f"[系统] NPC '{profile.name}' ({profile.id}) 已创建\n"
            f"性格: {profile.personality}\n"
            f"外貌: {profile.appearance or '未知'}"
        )

    def _handle_import_character(self, directive: str) -> str:
        inner = directive[1:-1]
        parts = inner.split(" ", 1)
        if len(parts) < 2:
            return "[系统] 用法: {导入角色 角色卡名称或路径}"
        name_or_path = parts[1].strip()
        profile = preset_load_character(name_or_path)
        if profile is None:
            available = preset_list_characters()
            hint = f"\n可用的角色预设: {', '.join(available)}" if available else ""
            return f"[系统] 未找到角色卡 '{name_or_path}'{hint}"
        self._characters.create_character(profile)
        if self._session:
            self._session.characters[profile.id] = profile
        return (
            f"[系统] 角色 '{profile.name}' ({profile.id}) 已导入\n"
            f"类型: {profile.character_type}\n"
            f"性格: {profile.personality[:80]}...\n"
            f"技能: {', '.join(f'{k}({v})' for k, v in list(profile.skills.items())[:6])}"
        )

    def _handle_list_character_presets(self) -> str:
        chars = preset_list_characters()
        if not chars:
            return "[系统] 没有可用的角色预设。请在 presets/characters/ 文件夹中放入 JSON 角色卡。"
        lines = ["[系统] 可用的角色预设:"]
        for c in chars:
            lines.append(f"  · {c}")
        return "\n".join(lines)

    def _handle_import_world(self, directive: str) -> str:
        inner = directive[1:-1]
        parts = inner.split(" ", 1)
        if len(parts) < 2:
            return "[系统] 用法: {导入世界观 世界观名称或路径}"
        name_or_path = parts[1].strip()
        bg = preset_load_world(name_or_path)
        if bg is None:
            available = preset_list_worlds()
            hint = f"\n可用的世界观预设: {', '.join(available)}" if available else ""
            return f"[系统] 未找到世界观 '{name_or_path}'{hint}"
        if self._session:
            self._session.campaign_background = bg
        self._context.set_campaign_background(bg)
        parts_text = []
        parts_text.append(f"[系统] 世界观 '{name_or_path}' 已导入")
        parts_text.append(f"背景: {bg.world_setting[:100]}...")
        if bg.factions:
            parts_text.append(f"势力: {', '.join(f.get('name', '?') for f in bg.factions[:5])}")
        if bg.important_locations:
            parts_text.append(f"主要地点: {', '.join(l.get('name', '?') for l in bg.important_locations[:5])}")
        return "\n".join(parts_text)

    def _handle_list_world_presets(self) -> str:
        worlds = preset_list_worlds()
        if not worlds:
            return "[系统] 没有可用的世界观预设。请在 presets/worlds/ 文件夹中放入 JSON 世界观文件。"
        lines = ["[系统] 可用的世界观预设:"]
        for w in worlds:
            lines.append(f"  · {w}")
        return "\n".join(lines)

    def _handle_pc_input(self, user_input: str) -> str:
        au, directive = parse_pc_input(user_input)

        if au is not None:
            au.character_id = self._pc_id
            self._process_action_unit(au)

        if directive is not None:
            if directive.content.startswith("检定 "):
                check_result = self._handle_skill_check(
                    f"{{检定 {directive.content[3:]}}}"
                )
                return check_result

        self._last_judgment = self._judgment_engine.judge()

        output = ""
        if au is not None:
            output += self._format_action_unit(au)
        output += f"\n[判断] → {self._last_judgment.next_speaker}"
        return output

    def _handle_save(self) -> str:
        if self._session is None:
            return "[系统] 没有可保存的会话"
        self._session.updated_at = ""
        persist_save(self._session)
        return f"[系统] 游戏已保存到 ./saves/{self._session.name}.json"

    def _handle_skill_check(self, directive: str) -> str:
        if self._pc_id is None:
            return "[系统] 未设置 PC"

        pc_skills = {}
        if self._session and self._pc_id in self._session.characters:
            pc_skills = self._session.characters[self._pc_id].skills

        skill_name = directive[1:-1]
        if skill_name.startswith("检定 "):
            skill_name = skill_name[3:]

        result = self._skill_handler.handle_directive(
            f"检定 {skill_name}", self._rules, pc_skills
        )

        if result is None:
            return "[系统] 无效的检定指令"

        return result.result_description

    def trigger_checkpoint(self, stage_label: str = "") -> str:
        if self._session is None:
            return "[系统] 无活动会话"
        if not stage_label:
            stage_label = f"检查点-{len(self._session.checkpoints) + 1}"

        all_dialogue = "\n".join(
            f"[{d.character_id}]: {d.dialogue}"
            for d in self._dialogue_log.history()
        )

        cp = self._checkpoint_manager.trigger_checkpoint(
            stage_label=stage_label,
            current_context=all_dialogue,
            character_profiles=self._session.characters,
        )
        self._session.checkpoints.append(cp)
        return f"[系统] 检查点已创建: {stage_label}\n摘要: {cp.summary}"

    def save_to_file(self, filepath: str | None = None):
        if self._session:
            persist_save(self._session, filepath)

    @staticmethod
    def load_from_file(filepath: str):
        return persist_load(filepath)

    def _format_action_unit(self, au: ActionUnit) -> str:
        lines = []
        label = au.character_id or "环境"
        if au.character_id and self._characters.get_profile(au.character_id):
            label = self._characters.get_profile(au.character_id).name
        elif au.character_id is None:
            label = "🌍 环境"

        if au.dialogue:
            lines.append(f'[{label}] 说: "{au.dialogue}"')
        if au.action:
            lines.append(f"[{label}] {au.action}")
        if au.inner_thought:
            lines.append(f"[{label}] (内心: {au.inner_thought})")
        return "\n".join(lines) if lines else f"[{label}] ..."

    def _process_action_unit(self, au: ActionUnit):
        if au.entered:
            campaign_ctx = {}
            if self._session and self._session.campaign_background:
                cb = self._session.campaign_background
                campaign_ctx = {
                    "world_setting": cb.world_setting,
                    "initial_situation": cb.initial_situation,
                }
            for cid in au.entered:
                if self._characters.get_profile(cid) is None:
                    profile = self._llm.create_npc_profile(
                        cid, "新登场角色", campaign_ctx
                    )
                    self._characters.create_character(profile)
                    if self._session:
                        self._session.characters[profile.id] = profile

        self._scene.process_action_unit(au)
        self._characters.append_context(
            au.character_id or "environment", au
        )
        if au.dialogue:
            self._dialogue_log.append(
                au.character_id or "environment", au.dialogue
            )

    def _format_present(self) -> str:
        present = self._scene.get_present()
        if not present:
            return "[在场] 无"
        names = []
        for cid in present:
            profile = self._characters.get_profile(cid)
            if profile:
                names.append(f"{profile.name}({cid})")
            else:
                names.append(cid)
        return f"[在场] {', '.join(names)}"
