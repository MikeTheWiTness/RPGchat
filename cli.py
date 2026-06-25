#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    ██████╗ ██████╗  ██████╗  ██████╗██╗  ██╗ █████╗ ████████╗
║    ██╔══██╗██╔══██╗██╔════╝ ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
║    ██████╔╝██████╔╝██║  ███╗██║     ███████║███████║   ██║
║    ██╔══██╗██╔═══╝ ██║   ██║██║     ██╔══██║██╔══██║   ██║
║    ██║  ██║██║     ╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║
║    ╚═╝  ╚═╝╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
║                                                          ║
║              AI 驱动的 TRPG 跑团系统 v0.1.0                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

PRESET_BACKGROUNDS = {
    "1": {
        "name": "奇幻酒馆开局",
        "text": (
            "一个中世纪奇幻世界。北方王国和南方帝国经历了十年战争后签订了和平条约。"
            "冒险者们在边境城镇铁炉镇的狮鹫酒馆聚集，各自怀着不同的目的。"
            "酒馆老板是一位退役的冒险者，传闻他知晓一个古老地下城的秘密入口。"
        ),
    },
    "2": {
        "name": "克苏鲁调查员",
        "text": (
            "1920年代，美国阿卡姆市。一系列离奇的失踪案引起了当地报社的注意。"
            "调查员们被各自的线人引导至此，发现这些事件与密斯卡塔尼克大学的"
            "一位神秘教授有关。空气中弥漫着不安的气息，似乎有什么不该存在的东西正在苏醒。"
        ),
    },
    "3": {
        "name": "赛博朋克边缘行者",
        "text": (
            "2077年，新东京。巨型企业控制着城市的每一个角落，街头佣兵在夹缝中求生。"
            "你们是一支小型边缘行者小队，刚刚接到了一单神秘委托——"
            "潜入荒坂集团数据中心，窃取一份代号为'黑日'的加密文件。"
        ),
    },
}


def main():
    from rpg_chat.llm import create_llm_gateway
    from rpg_chat.store import CharacterStore
    from rpg_chat.environment import DialogueLog, EnvironmentStore
    from rpg_chat.scene import SceneTracker
    from rpg_chat.context import ContextAssembler
    from rpg_chat.game_loop import GameLoop, GameLoopConfig
    from rpg_chat.types import CharacterProfile
    from rpg_chat.persistence import list_saves, load as load_game

    print(BANNER)
    print("欢迎来到 AI 跑团世界！\n")

    gateway = create_llm_gateway()
    cs = CharacterStore()
    dl = DialogueLog()
    es = EnvironmentStore()
    st = SceneTracker()
    ca = ContextAssembler(cs, dl, es, st)

    config = GameLoopConfig()
    engine = GameLoop(gateway, cs, dl, es, st, ca, config)

    while True:
        print("┌─────────────────────────────────────────────┐")
        print("│  1. 新建游戏                                  │")
        print("│  2. 加载存档                                  │")
        print("│  3. 退出                                      │")
        print("└─────────────────────────────────────────────┘")
        choice = input("\n> ").strip()

        if choice == "1":
            _new_game(engine, cs, st, ca, config)
            _game_loop(engine)
            break
        elif choice == "2":
            if _load_game(engine, cs, st, ca, config):
                _game_loop(engine)
                break
        elif choice == "3":
            print("\n再见，冒险者！")
            break
        else:
            print("无效选择，请输入 1/2/3")



def _create_pc_profile(module_name=""):
    """交互式创建 PC 角色档案 — 支持从预设加载或手动创建。
    module_name: 若提供，模组内角色将排在前面并标注"(模组内)"。"""
    from rpg_chat.preset_loader import list_characters, build_pc_from_preset, list_module_characters

    print("\n━━━ PC 角色创建 ━━━")
    print("  1. 手动创建（快速）")
    print("  2. 从角色预设加载（推荐，有完整档案）")
    choice = input("\n> ").strip()

    if choice == "2":
        chars = list_characters()
        if not chars:
            print("\n[系统] 没有可用的角色预设，切换为手动创建。")
        else:
            # 模组内角色优先，按角色名去重

            # 按 ID 去重：模组角色优先保留，全局预设中同 ID 者剔除
            mod_ids_to_path: dict[str, str] = {}  # 角色id → 模组内文件路径
            if module_name:
                from pathlib import Path
                module_chars_dir = Path("presets/modules") / module_name / "characters"
                for mc in list_module_characters(module_name):
                    mc_path = module_chars_dir / f"{mc}.json"
                    p = build_pc_from_preset(str(mc_path))
                    if p:
                        mod_ids_to_path[p.id] = str(mc_path)

            seen_ids: set[str] = set()
            deduped: list[tuple[str, bool, str]] = []  # (preset_name, is_module, display_desc)
            for c in chars:
                profile = build_pc_from_preset(c)
                if profile is None:
                    continue
                cid = profile.id
                if cid in seen_ids:
                    continue
                is_module = cid in mod_ids_to_path
                seen_ids.add(cid)
                # 模组内角色用模组版本的数据显示（更准确）
                display_profile = profile
                if is_module:
                    mp = build_pc_from_preset(mod_ids_to_path[cid])
                    if mp:
                        display_profile = mp
                occ = display_profile.identity.get("occupation", "") if display_profile.identity else ""
                desc = f" — {occ}" if occ else (f" — {display_profile.personality[:30]}..." if display_profile.personality else "")
                deduped.append((c, is_module, desc))

            deduped.sort(key=lambda x: (not x[1], x[0]))

            print("\n可选角色预设：")
            for i, (c, is_module, desc) in enumerate(deduped, 1):
                tag = " (模组内)" if is_module else ""
                print(f"  {i}. {c}{tag}{desc}")
            print("  0. 返回手动创建")
            p_choice = input("\n输入预设序号: ").strip()
            try:
                idx = int(p_choice)
                if 1 <= idx <= len(deduped):
                    preset_name = deduped[idx - 1][0]
                    print(f"\n已选择: {preset_name}")
                    name_ov = input(f"角色名称 (回车保留 '{preset_name}'): ").strip()
                    profile = build_pc_from_preset(preset_name, name_override=name_ov or "")
                    if profile:
                        print(f"PC 角色 '{profile.name}' 已从预设加载（{len(profile.skills)} 技能, {len(profile.attributes)} 属性）")
                        return profile
            except (ValueError, IndexError):
                pass
            print("无效选择，切换为手动创建。")

    pc_name = input("角色名称: ").strip() or "冒险者"
    pc_personality = input("角色性格（如: 勇敢的战士/狡猾的盗贼/睿智的法师）: ").strip() or "勇敢的冒险者"
    pc_skills_str = input("关键技能（用逗号分隔，如: 剑术,侦查,潜行）: ").strip()
    pc_skills = {}
    if pc_skills_str:
        for skill in pc_skills_str.split(","):
            skill = skill.strip()
            if skill:
                pc_skills[skill] = 60

    from rpg_chat.types import CharacterProfile
    return CharacterProfile(
        id="pc_main",
        name=pc_name,
        character_type="pc",
        personality=pc_personality,
        skills=pc_skills,
    )


def _new_game(engine, cs, st, ca, config):
    from rpg_chat.types import CharacterProfile
    from rpg_chat.preset_loader import list_modules

    print("\n═══ 创建新游戏 ═══\n")
    print("选择游戏类型：")
    print("  1. 自定义战役")
    print("  2. 加载模组（完整冒险包）")
    type_choice = input("\n> ").strip()

    if type_choice == "2":
        modules = list_modules()
        if not modules:
            print("\n[系统] 没有可用的模组。请在 presets/modules/ 放入模组文件夹。")
            return
        print("\n可用模组：")
        for i, m in enumerate(modules, 1):
            print(f"  {i}. {m}")
        m_choice = input("\n输入模组序号: ").strip()
        try:
            idx = int(m_choice) - 1
            module_name = modules[idx]
        except (ValueError, IndexError):
            print("无效选择，返回主菜单。")
            return

        print("\n选择运行模式：")
        print("  1. 玩家参与模式（扮演角色互动）")
        print("  2. 玩家空缺模式（自动推演，导演视角）")
        mode_choice = input("\n> ").strip()
        absent_mode = mode_choice == "2"

        if absent_mode:
            print("\n━━━ 玩家空缺模式 ━━━")
            print("故事将自动推演，你以导演视角参与。")
            print("随时可输入自由文本作为环境描述来干预剧情，或使用 {} 指令。")
            print("\n正在加载模组并生成初始场景...\n")
            output = engine.new_game_with_module(
                name=f"{module_name}-空缺",
                module_name=module_name,
            )
            print(output)
            return

        pc = _create_pc_profile(module_name)

        print("\n正在加载模组并生成初始场景...\n")
        output = engine.new_game_with_module(
            name=f"{pc.name}的{module_name}",
            module_name=module_name,
            pc_profile=pc,
        )
        print(output)
        return

    print("\n选择运行模式：")
    print("  1. 玩家参与模式（扮演角色互动）")
    print("  2. 玩家空缺模式（自动推演，导演视角）")
    mode_choice = input("\n> ").strip()
    absent_mode = mode_choice == "2"

    print("\n选择战役背景（输入序号，或输入 c 自定义）：")
    for key, preset in PRESET_BACKGROUNDS.items():
        print(f"  {key}. {preset['name']}")
        print(f"     {preset['text'][:60]}...")
    print("  c. 自定义战役背景")

    bg_choice = input("\n> ").strip().lower()
    if bg_choice == "c":
        print("\n请输入战役背景描述（支持短描述或长篇设定）：")
        campaign_input = input("> ").strip()
    elif bg_choice in PRESET_BACKGROUNDS:
        campaign_input = PRESET_BACKGROUNDS[bg_choice]["text"]
        print(f"\n已选择: {PRESET_BACKGROUNDS[bg_choice]['name']}")
    else:
        campaign_input = PRESET_BACKGROUNDS["1"]["text"]
        print(f"\n默认选择: {PRESET_BACKGROUNDS['1']['name']}")

    if absent_mode:
        print("\n━━━ 玩家空缺模式 ━━━")
        print("故事将自动推演，你以导演视角参与。")
        print("随时可输入自由文本作为环境描述来干预剧情，或使用 {} 指令。")
        print("\n选择规则系统：")
        print("  1. 纯叙事模式（推荐，空缺模式不支持骰子检定）")
        rules_choice = input("\n> ").strip()
        mechanics = "pure-narrative"
        rules_system = ""
        if rules_choice != "1":
            print("已强制使用纯叙事模式（玩家空缺模式不启用骰子检定）")

        print("\n正在生成初始场景...\n")
        output = engine.new_game_absent(
            name="空缺推演",
            campaign_input=campaign_input,
            mechanics_mode=mechanics,
        )
        print(output)
        return

    pc = _create_pc_profile()

    print("\n选择规则系统：")
    print("  1. 纯叙事模式（推荐）")
    print("  2. 轻量规则（d20）")
    rules_choice = input("\n> ").strip()
    mechanics = "pure-narrative"
    rules_system = ""
    if rules_choice == "2":
        mechanics = "light-rules"
        rules_system = "d20"

    print("\n正在生成初始场景...\n")
    output = engine.new_game(
        name=f"{pc.name}的冒险",
        campaign_input=campaign_input,
        pc_profile=pc,
        mechanics_mode=mechanics,
        rules_system=rules_system,
    )
    print(output)


def _load_game(engine, cs, st, ca, config):
    saves = list_saves()
    if not saves:
        print("\n没有找到存档文件。")
        return False

    print("\n═══ 存档列表 ═══")
    for i, path in enumerate(saves, 1):
        name = os.path.basename(path).replace(".json", "")
        print(f"  {i}. {name}")
    print("  0. 返回")

    choice = input("\n> ").strip()
    try:
        idx = int(choice)
        if idx == 0:
            return False
        if 1 <= idx <= len(saves):
            session = load_game(saves[idx - 1])
            print(f"\n已加载存档: {session.name}")
            return True
    except (ValueError, IndexError):
        pass
    return False


def _game_loop(engine):
    print("\n" + "═" * 50)
    print("游戏开始！")
    is_absent = engine.session is not None and engine.session.mode == "player-absent"
    if is_absent:
        print("━ 玩家空缺模式 ━")
        print("  自由文本         — 作为环境描述干预剧情")
        print("  {继续}           — 推进下一步（NPC/环境）")
        print("  {检查点}         — 提议检查点（需确认）")
        print("  {保存}           — 保存游戏")
        print("  {查看在场}       — 查看在场人物")
        print("  {创建NPC 名 描述} — 创建NPC角色卡")
        print("  {修改角色 ID 字段 值} — 修改角色档案")
        print("  {导入角色 名称}    — 从 presets/characters/ 导入角色")
        print("  {导入世界观 名称}   — 从 presets/worlds/ 导入世界观")
        print("  {列出角色预设}     — 查看可导入的角色")
        print("  {列出世界观预设}   — 查看可导入的世界观")
        print("  {列出模组}       — 查看可用的模组")
    else:
        print("━ 输入格式:")
        print('  【对话】        — 角色发言（支持多个【】标记）')
        print("  行动描述         — 角色行动")
        print("  （内心活动）     — 角色内心")
        print("  {继续}           — 采纳判断机制")
        print("  {检定 技能名}    — 执行技能检定")
        print("  {保存}           — 保存游戏")
        print("  {查看在场}       — 查看在场人物")
        print('  {创建NPC 名 描述} — 创建NPC角色卡')
        print('  {修改角色 ID 字段 值} — 修改角色档案')
        print('  {导入角色 名称}    — 从 presets/characters/ 导入角色')
        print('  {导入世界观 名称}   — 从 presets/worlds/ 导入世界观')
        print('  {列出角色预设}     — 查看可导入的角色')
        print('  {列出世界观预设}   — 查看可导入的世界观')
        print('  {列出模组}       — 查看可用的模组')
    print("  /help            — 显示帮助")
    print("  /quit            — 退出游戏")
    print("═" * 50 + "\n")

    while True:
        try:
            user_input = input("🎮 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n正在保存并退出...")
            engine.save_to_file()
            print("再见，冒险者！")
            break

        if not user_input:
            continue

        if user_input == "/help":
            _show_help()
            continue

        if user_input == "/quit":
            save_choice = input("是否保存游戏？(y/n): ").strip().lower()
            if save_choice == "y":
                engine.save_to_file()
                print("游戏已保存。")
            print("再见，冒险者！")
            break

        if user_input.startswith("{") and user_input != "{查看在场}" and user_input != "{列出角色预设}" and user_input != "{列出世界观预设}" and user_input != "{列出模组}":
            pass  # 指令类不需要思考提示
        else:
            print("⏳ 思考中...", end="", flush=True)
        response = engine.handle_input(user_input, on_step=lambda sp, txt: print(f"\n{txt}", flush=True))


def _show_help():
    print("""
┌────────────────────────────────────────────┐
│  操作指南                                    │
├────────────────────────────────────────────┤
│  【对话内容】   — PC 说出对话                │
│  行动描述       — PC 执行动作                │
│  （内心活动）   — PC 的内心想法（仅 GM 可见） │
│  行动【对话】   — 边说边做                    │
│  行动【对话】（想）— 边说边做边想             │
│                                            │
│  支持多段对话:                                │
│  说【你好】走过去【注意安全】（担心）          │
│                                            │
│  {继续}         — 让 NPC/环境继续            │
│  {检定 技能}    — 投骰检定（需规则模式）      │
│  {保存}         — 保存当前进度               │
│  {查看在场}     — 查看场景中所有角色          │
│  {创建NPC 名 描述} — 创建NPC角色             │
│  {修改角色 ID 字段 值} — 修改角色档案          │
│  {导入角色 名称/路径} — 导入JSON角色卡        │
│  {导入世界观 名称/路径} — 导入JSON世界观      │
│  {列出角色预设} — 浏览可用的角色卡            │
│  {列出世界观预设} — 浏览可用的世界观          │
│                                            │
│  /help          — 显示本帮助                 │
│  /quit          — 退出游戏                   │
└────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    main()
