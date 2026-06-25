from dataclasses import dataclass, field
from typing import Optional

from rpg_chat.types import (
    ActionUnit, AgentDirective, CampaignBackground, CharacterProfile,
    GameSession, JudgmentResult, RulesConfig, CheckResult, PlotOutline,
    Snapshot,
)
from rpg_chat.store import CharacterStore
from rpg_chat.environment import DialogueLog, EnvironmentStore
from rpg_chat.scene import SceneTracker
from rpg_chat.context import ContextAssembler
from rpg_chat.parser import parse_pc_input, split_narrative
from rpg_chat.llm import LLMGateway
from rpg_chat.judgment import JudgmentEngine
from rpg_chat.rules import SkillCheckHandler, PRESETS
from rpg_chat.campaign import CampaignBackgroundParser
from rpg_chat.checkpoint import CheckpointManager
from rpg_chat.confirmation import ConfirmationManager, ConfirmationType
from rpg_chat.persistence import save as persist_save, load as persist_load
from rpg_chat.plot_tracker import PlotTracker
from rpg_chat.preset_loader import (
    load_character as preset_load_character,
    list_characters as preset_list_characters,
    load_world as preset_load_world,
    list_worlds as preset_list_worlds,
    load_module as preset_load_module,
    list_modules as preset_list_modules,
    build_plot_outline_from_dict,
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
    env_force_lambda: float = 0.15


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
            env_force_lambda=self._config.env_force_lambda,
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
        self._confirmation = ConfirmationManager()
        self._plot_tracker: PlotTracker | None = None
        self._snapshots: list[Snapshot] = []
        self._snapshot_seq = 0
        self._MAX_SNAPSHOTS = 200

    @property
    def session(self) -> Optional[GameSession]:
        return self._session

    @property
    def present_characters(self) -> list[str]:
        return self._scene.get_present()

    @property
    def last_judgment(self) -> Optional[JudgmentResult]:
        return self._last_judgment

    def has_pending_confirmation(self) -> bool:
        return self._confirmation.has_pending()

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
        self._snapshots = []
        self._snapshot_seq = 0

        return self._initialize_scene(background)

    def _initialize_scene_from_text(self, scene_text: str, background) -> str:
        """用固定文本初始化场景，不走 LLM 环境生成。"""
        self._context.set_campaign_background(background)
        self._sync_director_intents_to_context()
        self._sync_plot_to_context()
        entered_ids = list(self._scene.get_present())
        au = ActionUnit(
            character_id=None,
            action=scene_text,
            entered=entered_ids,
        )
        self._process_action_unit(au)
        self._last_judgment = self._judgment_engine.judge()
        result_text = self._format_action_unit(au)
        present_text = self._format_present()
        next_text = (
            f"[判断] 下一个发言: {self._resolve_speaker_name(self._last_judgment.next_speaker)} "
            f"({self._last_judgment.reason})"
        )
        return f"{result_text}\n{present_text}\n{next_text}"

    def new_game_absent(
        self,
        name: str,
        campaign_input: str,
        mechanics_mode: str = "pure-narrative",
    ) -> str:
        background = self._campaign_parser.parse(campaign_input)

        session = GameSession(
            id=f"session_{name}",
            name=name,
            mode="player-absent",
            mechanics_mode=mechanics_mode,
            campaign_background=background,
        )

        self._pc_id = None
        self._session = session
        self._rules = None
        self._running = True

        return self._initialize_scene(background)

    def _initialize_scene(self, background) -> str:
        self._context.set_campaign_background(background)
        self._sync_director_intents_to_context()
        self._sync_plot_to_context()
        env_au = self._judgment_engine.generate_environment()
        self._process_action_unit(env_au)
        self._last_judgment = self._judgment_engine.judge()
        result_text = self._format_action_unit(env_au)
        present_text = self._format_present()
        next_text = (
            f"[判断] 下一个发言: {self._resolve_speaker_name(self._last_judgment.next_speaker)} "
            f"({self._last_judgment.reason})"
        )
        return f"{result_text}\n{present_text}\n{next_text}"

    def new_game_with_module(
        self,
        name: str,
        module_name: str,
        pc_profile: Optional[CharacterProfile] = None,
        custom_outline_text: str = "",
    ) -> str:
        module = preset_load_module(module_name)
        if module is None:
            return f"[系统] 未找到模组 '{module_name}'"

        background = module["world"]
        absent_mode = pc_profile is None

        rules = None
        mechanics_mode = module.get("mechanics_mode") or "pure-narrative"
        rules_system = module.get("rules_system") or ""
        if mechanics_mode == "light-rules" and rules_system:
            rules = PRESETS.get(rules_system)

        session = GameSession(
            id=f"session_{name}",
            name=name,
            mode="player-absent" if absent_mode else "player-present",
            mechanics_mode=mechanics_mode,
            campaign_background=background,
            rules_config=rules,
        )

        if absent_mode:
            self._pc_id = None
        else:
            self._characters.create_character(pc_profile)
            session.characters[pc_profile.id] = pc_profile
            self._pc_id = pc_profile.id

        for profile in module["characters"]:
            if not absent_mode and pc_profile and profile.name == pc_profile.name:
                continue
            self._characters.create_character(profile)
            session.characters[profile.id] = profile

        module_npc_ids = [
            profile.id
            for profile in module["characters"]
            if (absent_mode or not pc_profile or profile.name != pc_profile.name)
        ]
        if not absent_mode and pc_profile:
            module_npc_ids.append(pc_profile.id)
        self._scene.add_characters(module_npc_ids)

        self._session = session
        self._rules = rules
        self._running = True
        self._snapshots = []
        self._snapshot_seq = 0

        # 初始化剧情追踪器
        plot_outline = module.get("plot_outline")
        if custom_outline_text:
            po_dict = self._llm.build_plot_outline_from_text(custom_outline_text)
            custom_outline = build_plot_outline_from_dict(po_dict)
            if custom_outline and custom_outline.chapters:
                plot_outline = custom_outline
        if plot_outline:
            self._plot_tracker = PlotTracker.from_outline(plot_outline)
            session.plot_outline = plot_outline

        initial_situation = module.get("initial_situation", "")
        if initial_situation:
            return self._initialize_scene_from_text(initial_situation, background)
        return self._initialize_scene(background)

    def handle_input(self, user_input: str, on_step=None) -> str:
        """处理用户输入。on_step(speaker_name, text) 用于流式输出。"""
        if not self._running:
            return "游戏未运行"

        user_input = user_input.strip()

        if user_input == "{确认}" or user_input.startswith("{确认 "):
            return self._handle_confirm(user_input)

        if user_input == "{拒绝}":
            return self._handle_reject()

        if self._confirmation.has_pending():
            pending = self._confirmation.get_pending()
            return (
                f"[系统] 当前有待确认事项，请先处理：\n"
                f"  类型: {pending.type.value}\n"
                f"  内容: {pending.description}\n"
                f"输入 {{确认}} 或 {{拒绝}}"
            )

        if user_input == "{继续}":
            result = self._handle_continue(on_step=on_step)
            result += self._auto_chain(on_step=on_step)
            return result

        if user_input == "{保存}":
            return self._handle_save()

        if user_input == "{查看在场}":
            return self._format_present()

        if user_input == "{检查点}" or user_input.startswith("{检查点 "):
            return self._handle_checkpoint_directive(user_input)

        if user_input.startswith("{检定 "):
            return self._handle_skill_check(user_input)

        if user_input.startswith("{创建NPC "):
            return self._handle_create_npc(user_input)

        if user_input.startswith("{修改角色 "):
            return self._handle_modify_character(user_input)

        if user_input.startswith("{导入角色 "):
            return self._handle_import_character(user_input)

        if user_input == "{列出角色预设}":
            return self._handle_list_character_presets()

        if user_input.startswith("{导入世界观 "):
            return self._handle_import_world(user_input)

        if user_input == "{列出世界观预设}":
            return self._handle_list_world_presets()

        if user_input == "{列出模组}":
            return self._handle_list_modules()

        if user_input == "{查看意图}":
            return self._handle_view_intents()

        if user_input == "{清除意图}":
            return self._handle_clear_intents()

        if user_input.startswith("{意图 ") or user_input.startswith("{删除意图 "):
            return self._handle_remove_intent(user_input)

        if user_input == "{历史}" or user_input == "{快照列表}":
            return self._handle_history()

        if user_input.startswith("{回滚 ") or user_input == "{回滚}":
            return self._handle_rollback(user_input)

        if user_input == "{大纲}":
            return self._handle_view_outline()

        if user_input.startswith("{设定大纲 ") or user_input == "{设定大纲}":
            return self._handle_set_outline(user_input)

        result = self._handle_pc_input(user_input, on_step=on_step)
        result += self._auto_chain(on_step=on_step)
        return result

    def _handle_continue(self, on_step=None) -> str:
        if self._last_judgment.force_environment:
            next_speaker = "environment"
        else:
            next_speaker = self._last_judgment.next_speaker

        if next_speaker == "environment":
            gm_hint = self._last_judgment.reason if self._last_judgment else ""
            au = self._judgment_engine.generate_environment(gm_hint)
            self._process_action_unit(au)
            self._last_judgment = self._judgment_engine.judge()
            output = self._format_action_unit(au)
            output += f"\n[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）"
            if on_step:
                on_step("环境", output)
            return output

        if next_speaker == self._pc_id:
            return "[系统] 轮到 PC 发言，请输入角色动作。"

        # NPC 发言
        profile = self._characters.get_profile(next_speaker)
        if profile is None:
            profile = self._characters.create_npc_on_the_fly(next_speaker, "未知角色")
            if self._session:
                self._session.characters[profile.id] = profile
        ctx = self._context.assemble_for_character(next_speaker)
        au = self._llm.generate_npc_action_unit(ctx)
        output, _ = self._process_and_format(au, on_step=on_step)

        self._last_judgment = self._judgment_engine.judge()
        output += f"\n[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）"
        if on_step:
            on_step("判断", f"[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）")
        return output

    def _auto_chain(self, on_step=None) -> str:
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
            step = self._generate_step(next_speaker, on_step=on_step)
            output_parts.append(step)
        return "\n" + "\n".join(output_parts) if output_parts else ""

    def _generate_step(self, speaker_id: str, on_step=None) -> str:
        if speaker_id == "environment":
            gm_hint = self._last_judgment.reason if self._last_judgment else ""
            au = self._judgment_engine.generate_environment(gm_hint)
            self._process_action_unit(au)
            self._last_judgment = self._judgment_engine.judge()
            output = self._format_action_unit(au)
            output += f"\n[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）"
            if on_step:
                on_step("环境", output)
            return output

        profile = self._characters.get_profile(speaker_id)
        if profile is None:
            profile = self._characters.create_npc_on_the_fly(speaker_id, "未知角色")
            if self._session:
                self._session.characters[profile.id] = profile
        ctx = self._context.assemble_for_character(speaker_id)
        au = self._llm.generate_npc_action_unit(ctx)
        output, _ = self._process_and_format(au, on_step=on_step)

        self._last_judgment = self._judgment_engine.judge()
        output += f"\n[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）"
        if on_step:
            on_step("判断", f"[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）")
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

    def _handle_modify_character(self, directive: str) -> str:
        inner = directive[1:-1]
        parts = inner.split(" ", 2)
        if len(parts) < 3:
            return "[系统] 用法: {修改角色 角色ID 字段名 值}"
        char_id = parts[1]
        rest = parts[2]
        field_parts = rest.split(" ", 1)
        if len(field_parts) < 2:
            return "[系统] 用法: {修改角色 角色ID 字段名 值}"
        field_name = field_parts[0]
        value_str = field_parts[1]

        if self._characters.get_profile(char_id) is None:
            return f"[系统] 角色 '{char_id}' 不存在"

        import json as _json
        try:
            value = _json.loads(value_str)
        except (_json.JSONDecodeError, ValueError):
            value = value_str

        try:
            self._characters.update_profile(char_id, {field_name: value})
        except KeyError as e:
            return f"[系统] {e}"

        profile = self._characters.get_profile(char_id)
        return f"[系统] 角色 '{profile.name}' ({char_id}) 的 '{field_name}' 已修改"

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

    def _handle_list_modules(self) -> str:
        modules = preset_list_modules()
        if not modules:
            return "[系统] 没有可用的模组。请在 presets/modules/ 文件夹中放入模组文件夹。"
        lines = ["[系统] 可用的模组:"]
        for m in modules:
            module = preset_load_module(m)
            desc = ""
            if module and module.get("initial_situation"):
                desc = f" — {module['initial_situation'][:40]}..."
            lines.append(f"  · {m}{desc}")
        lines.append("\n使用 new_game_with_module() 开始模组游戏")
        return "\n".join(lines)

    def _handle_pc_input(self, user_input: str, on_step=None) -> str:
        if self._session is not None and self._session.mode == "player-absent":
            # 存入导演意图栈
            self._session.director_intents.append(user_input)
            self._sync_director_intents_to_context()

            au = ActionUnit(character_id=None, action=user_input)
            self._process_action_unit(au)
            self._last_judgment = self._judgment_engine.judge()
            output = self._format_action_unit(au)
            output += f"\n[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）"
            if on_step:
                on_step("环境", output)
            return output

        au, directive = parse_pc_input(user_input)

        if directive is not None and directive.content.startswith("检定 "):
            return self._handle_skill_check(
                f"{{检定 {directive.content[3:]}}}"
            )

        if (
            au is not None
            and au.action is not None
            and self._rules is not None
            and self._pc_id is not None
        ):
            check_output = self._try_embedded_check(au.action)
            if check_output is not None:
                return check_output

        if au is not None:
            au.character_id = self._pc_id
            self._process_action_unit(au)

        output = ""
        if au is not None:
            output += self._format_action_unit(au)
            if on_step:
                on_step(au.character_id or "环境", output)

            # PC 有动作 → GM 助手描述客观结果
            if au.action:
                campaign = ""
                if self._session and self._session.campaign_background:
                    campaign = self._session.campaign_background.world_setting[:500]
                result_au = self._llm.generate_pc_action_result(au.action, campaign)
                result_au.character_id = None
                self._process_action_unit(result_au)
                payload = self._format_action_unit(result_au)
                output += "\n" + payload
                if on_step:
                    on_step("环境", payload)

        self._last_judgment = self._judgment_engine.judge()
        speaker = self._resolve_speaker_name(self._last_judgment.next_speaker)
        output += f"\n[判断] → {speaker}（{self._last_judgment.reason}）"
        if on_step:
            on_step("判断", f"[判断] → {speaker}（{self._last_judgment.reason}）")
        return output

    def _try_embedded_check(self, pc_action: str) -> str | None:
        if self._session is None or self._pc_id is None:
            return None

        pc_profile = self._session.characters.get(self._pc_id)
        if pc_profile is None:
            return None

        rules_skills = self._rules.skills if self._rules else {}
        present = self._scene.get_present()

        check_judgment = self._llm.judge_check({
            "pc_action": pc_action,
            "pc_profile": pc_profile,
            "present_characters": present,
            "rules_skills": rules_skills,
        })

        if not check_judgment["needed"]:
            return None

        skill_name = check_judgment["skill"]
        dc = check_judgment["dc"]

        check_result = self._skill_handler.handle_directive(
            f"检定 {skill_name} {dc}", self._rules, pc_profile.skills
        )
        if check_result is None:
            return None

        au = self._llm.generate_pc_action_with_check(
            {
                "pc_action": pc_action,
                "pc_profile": pc_profile,
                "present_characters": present,
            },
            check_result,
        )
        au.character_id = self._pc_id
        self._process_action_unit(au)

        self._last_judgment = self._judgment_engine.judge()

        output = self._format_action_unit(au)
        output += (
            f"\n[检定] {skill_name} DC{dc} "
            f"d20={check_result.roll.rolls[0] if check_result.roll else '?'} "
            f"→ {'成功' if check_result.success else '失败'}"
        )
        output += f"\n[判断] → {self._resolve_speaker_name(self._last_judgment.next_speaker)}（{self._last_judgment.reason}）"
        return output

    def _handle_save(self) -> str:
        if self._session is None:
            return "[系统] 没有可保存的会话"
        self._session.updated_at = ""
        persist_save(self._session)
        return f"[系统] 游戏已保存到 ./saves/{self._session.name}.json"

    def _handle_checkpoint_directive(self, directive: str) -> str:
        inner = directive[1:-1].strip()
        parts = inner.split(" ", 1)
        stage_label = parts[1].strip() if len(parts) > 1 else ""
        return self.propose_checkpoint(stage_label)

    def _handle_skill_check(self, directive: str) -> str:
        if self._session is not None and self._session.mode == "player-absent":
            return "[系统] 玩家空缺模式不启用骰子检定"

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

    def propose_checkpoint(self, stage_label: str) -> str:
        if self._session is None:
            return "[系统] 无活动会话"
        req = self._confirmation.propose(
            ConfirmationType.CHECKPOINT,
            f"检查点: {stage_label}",
            {"stage_label": stage_label},
        )
        return (
            f"[系统] 检查点提议待确认: {stage_label}\n"
            f"  请求ID: {req.id}\n"
            f"输入 {{确认}} 执行，{{拒绝}} 取消"
        )

    def _handle_confirm(self, directive: str = "{确认}") -> str:
        pending = self._confirmation.get_pending()
        if pending is None:
            return "[系统] 当前无待确认事项"
        self._confirmation.confirm(pending.id)

        cleanup_chars: list[str] = []
        inner = directive[1:-1].strip()
        if inner.startswith("确认 "):
            cleanup_str = inner[3:].strip()
            cleanup_chars = [
                c.strip() for c in cleanup_str.split(",") if c.strip()
            ]

        if pending.type == ConfirmationType.CHECKPOINT:
            stage_label = pending.payload.get("stage_label", "")
            result = self.trigger_checkpoint(stage_label)
            if cleanup_chars:
                self._checkpoint_manager.clean_departed_contexts(cleanup_chars)
                result += f"\n[系统] 已清理离场角色上下文: {', '.join(cleanup_chars)}"
            return result
        return f"[系统] 已确认: {pending.description}"

    def _handle_reject(self) -> str:
        pending = self._confirmation.get_pending()
        if pending is None:
            return "[系统] 当前无待确认事项"
        self._confirmation.reject(pending.id)
        return f"[系统] 已拒绝: {pending.description}"

    def save_to_file(self, filepath: str | None = None):
        if self._session:
            persist_save(self._session, filepath)

    @staticmethod
    def load_from_file(filepath: str):
        return persist_load(filepath)

    def _resolve_speaker_name(self, speaker_id: str) -> str:
        """将发言者 ID 转为显示名称"""
        if speaker_id == "environment":
            return "🌍 环境"
        profile = self._characters.get_profile(speaker_id)
        if profile:
            return profile.name
        return speaker_id

    def _format_action_unit(self, au: ActionUnit) -> str:
        lines = []
        label = au.character_id or "环境"
        if au.character_id and self._characters.get_profile(au.character_id):
            label = self._characters.get_profile(au.character_id).name
        elif au.character_id is None:
            label = "🌍 环境"

        seq = getattr(au, "_seq", None)
        seq_prefix = f"#{seq} " if seq is not None else ""

        if au.dialogue:
            lines.append(f'{seq_prefix}[{label}] 说: "{au.dialogue}"')
        if au.action:
            lines.append(f"{seq_prefix}[{label}] {au.action}")
        if au.inner_thought:
            lines.append(f"{seq_prefix}[{label}] (内心: {au.inner_thought})")
        return "\n".join(lines) if lines else f"{seq_prefix}[{label}] ..."

    def _process_action_unit(self, au: ActionUnit):
        # 回滚锚点：先存快照，再处理动作单元
        seq = self._take_snapshot(self._describe_au(au))
        au._seq = seq
        self._apply_action_unit(au)

    def _apply_action_unit(self, au: ActionUnit, count: bool = True):
        """实际把动作单元写入各存储，不拍照（用于已统一拍照的多段叙述）。"""
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

        self._scene.process_action_unit(au, count=count)
        self._characters.append_context(
            au.character_id or "environment", au
        )
        # 环境动作单元也存入 environment_store
        if au.character_id is None and au.action:
            self._environment.add_action_unit(au)
        if au.dialogue:
            self._dialogue_log.append(
                au.character_id or "environment", au.dialogue
            )

    def _expand_narrative(self, au: ActionUnit) -> list[ActionUnit]:
        """若 au 含 narrative（_narrative 标记），拆成多段；否则原样返回 [au]。"""
        narrative = getattr(au, "_narrative", None)
        if not narrative:
            return [au]
        units = split_narrative(
            narrative,
            character_id=au.character_id,
            audience=au.audience,
            entered=au.entered,
            left=au.left,
        )
        return units if units else [au]

    def _process_and_format(self, au: ActionUnit, on_step=None) -> tuple[str, list[ActionUnit]]:
        """处理含 narrative 的 au：拆分、共享一次快照/序号、逐个写入、格式化。"""
        units = self._expand_narrative(au)
        # 整段 narrative 共享一次快照和一个序号；描述用首段
        desc = self._describe_au(units[0]) if units else self._describe_au(au)
        seq = self._take_snapshot(desc)
        for u in units:
            u._seq = seq
        output_parts = []
        for i, u in enumerate(units):
            # 整段 narrative 只算一次发言，所以只在第一段计数
            self._apply_action_unit(u, count=(i == 0))
            piece = self._format_action_unit(u)
            output_parts.append(piece)
            if on_step:
                on_step(u.character_id or "环境", piece)
        return "\n".join(output_parts), units

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

    def _sync_director_intents_to_context(self):
        if self._session:
            self._context.set_director_intents(self._session.director_intents)

    def _sync_plot_to_context(self):
        if self._plot_tracker:
            self._context.set_plot_context(self._plot_tracker.get_current_context())

    def _handle_view_intents(self) -> str:
        if self._session is None:
            return "[系统] 无活动会话"
        intents = self._session.director_intents
        if not intents:
            return "[系统] 当前无导演意图。输入自由文本即可添加导演意图。"
        lines = ["[系统] 当前导演意图:"]
        for i, text in enumerate(intents):
            lines.append(f"  {i+1}. {text}")
        lines.append("\n输入 {{清除意图}} 清空，或 {{意图 N}} 删除第 N 条。")
        return "\n".join(lines)

    def _handle_clear_intents(self) -> str:
        if self._session is None:
            return "[系统] 无活动会话"
        self._session.director_intents.clear()
        self._sync_director_intents_to_context()
        return "[系统] 导演意图已清除，剧情将回归模组默认方向。"

    def _handle_remove_intent(self, directive: str) -> str:
        if self._session is None:
            return "[系统] 无活动会话"
        inner = directive[1:-1]
        # 提取数字：{意图 3} 或 {删除意图 3}
        num_str = inner.replace("意图", "").replace("删除", "").strip()
        try:
            n = int(num_str)
        except ValueError:
            return "[系统] 用法: {意图 N} 或 {删除意图 N}，N 为序号"
        intents = self._session.director_intents
        if n < 1 or n > len(intents):
            return f"[系统] 序号超出范围（共 {len(intents)} 条）"
        removed = intents.pop(n - 1)
        self._sync_director_intents_to_context()
        return f"[系统] 已删除意图 #{n}: {removed}"

    # ===== 大纲覆盖 =====
    def _handle_view_outline(self) -> str:
        if not self._plot_tracker or not self._plot_tracker.outline:
            return "[系统] 当前无剧情大纲。可用 {设定大纲 你的剧情描述} 设定。"
        ctx = self._plot_tracker.get_current_context()
        return f"[系统] 当前剧情大纲:\n{ctx}\n\n可用 {{设定大纲 ...}} 覆盖，或继续推进。"

    def _handle_set_outline(self, directive: str) -> str:
        if self._session is None:
            return "[系统] 无活动会话"
        inner = directive[1:-1]
        text = inner.replace("设定大纲", "", 1).strip()
        if not text:
            return "[系统] 用法: {设定大纲 你的剧情描述}，将解析为章节式大纲并覆盖当前大纲。"
        po_dict = self._llm.build_plot_outline_from_text(text)
        outline = build_plot_outline_from_dict(po_dict)
        if outline is None or not outline.chapters:
            return f"[系统] 未能从输入解析出有效大纲。已保留原大纲。\n解析结果: {po_dict.get('summary', '')}"
        self._plot_tracker = PlotTracker.from_outline(outline)
        if self._session:
            self._session.plot_outline = outline
        self._sync_plot_to_context()
        ch_titles = " → ".join(c.title for c in outline.chapters)
        return (
            f"[系统] 剧情大纲已覆盖。\n"
            f"标题: {outline.title}\n"
            f"章节: {ch_titles}\n"
            f"结局方向: {len(outline.possible_endings)} 个\n"
            f"当前章节: {self._plot_tracker.get_current_chapter().title if self._plot_tracker.get_current_chapter() else '无'}"
        )

    # ===== 回滚机制 =====
    def _describe_au(self, au: ActionUnit) -> str:
        """生成动作单元的简短描述，用于快照列表。"""
        label = "环境"
        if au.character_id:
            p = self._characters.get_profile(au.character_id)
            if p:
                label = p.name
            else:
                label = au.character_id
        if au.dialogue:
            text = au.dialogue[:30]
            return f"[{label}] 说: \"{text}{'...' if len(au.dialogue) > 30 else ''}\""
        if au.action:
            text = au.action[:30]
            return f"[{label}] {text}{'...' if len(au.action) > 30 else ''}"
        if au.inner_thought:
            return f"[{label}] (内心)"
        if au.entered:
            return f"[{label}] 进入场景"
        return f"[{label}] ..."

    def _take_snapshot(self, description: str) -> int:
        """保存当前完整状态为快照。返回快照序号。"""
        import copy as _copy
        seq = self._snapshot_seq
        snap = Snapshot(
            sequence=seq,
            description=description,
            character_contexts=self._characters.snapshot_contexts(),
            environment_entries=self._environment.snapshot_entries(),
            dialogue_log=self._dialogue_log.snapshot_entries(),
            scene_state=self._scene.snapshot(),
            last_judgment=_copy.deepcopy(self._last_judgment),
            director_intents=list(self._session.director_intents) if self._session else [],
            plot_tracker_state=self._plot_tracker.snapshot() if self._plot_tracker else None,
        )
        self._snapshots.append(snap)
        self._snapshot_seq += 1
        # 上限控制
        if len(self._snapshots) > self._MAX_SNAPSHOTS:
            self._snapshots = self._snapshots[-self._MAX_SNAPSHOTS:]
        return seq

    def _restore_snapshot(self, snap: Snapshot):
        """从快照恢复所有状态。"""
        self._characters.restore_contexts(snap.character_contexts)
        self._environment.restore_entries(snap.environment_entries)
        self._dialogue_log.restore_entries(snap.dialogue_log)
        self._scene.restore(snap.scene_state)
        self._last_judgment = snap.last_judgment
        if self._session is not None:
            self._session.director_intents = list(snap.director_intents)
            self._sync_director_intents_to_context()
        if self._plot_tracker and snap.plot_tracker_state:
            self._plot_tracker.restore(snap.plot_tracker_state)
            self._sync_plot_to_context()

    def _handle_history(self) -> str:
        if not self._snapshots:
            return "[系统] 暂无历史记录。"
        lines = ["[系统] 最近的动作记录（直接输入序号或 {回滚 N} 回到该动作之前）:"]
        # 显示最近 20 条
        recent = self._snapshots[-20:]
        for snap in recent:
            lines.append(f"  #{snap.sequence}  {snap.description}")
        lines.append(f"\n共 {len(self._snapshots)} 条记录。回滚到第 N 条之前即撤销该动作及其后所有动作。")
        return "\n".join(lines)

    def _handle_rollback(self, directive: str) -> str:
        if not self._snapshots:
            return "[系统] 暂无历史记录可回滚。"
        inner = directive[1:-1]
        num_str = inner.replace("回滚", "").strip()
        try:
            n = int(num_str)
        except ValueError:
            return "[系统] 用法: {回滚 N}，N 为历史记录中的序号"
        # 找到序号为 n 的快照
        target = None
        for snap in self._snapshots:
            if snap.sequence == n:
                target = snap
                break
        if target is None:
            return f"[系统] 找不到序号 {n}。输入 {{历史}} 查看可用序号。"
        # 恢复到该快照（快照记录的是动作单元之前的状态）
        self._restore_snapshot(target)
        # 删除该快照之后的所有快照
        self._snapshots = [s for s in self._snapshots if s.sequence <= target.sequence]
        self._snapshot_seq = target.sequence + 1
        return (
            f"[系统] 已回滚到序号 {n}（{target.description}）之前的状态。\n"
            f"之后的 {0} 条记录已清除。输入 {{继续}} 重新推进剧情。"
        )
