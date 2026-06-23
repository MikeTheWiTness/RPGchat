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


def _new_game(engine, cs, st, ca, config):
    from rpg_chat.types import CharacterProfile

    print("\n═══ 创建新游戏 ═══\n")
    print("选择战役背景（输入序号，或输入 c 自定义）：")
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

    print("\n━━━ 角色创建 ━━━")
    pc_name = input("角色名称: ").strip() or "冒险者"
    pc_personality = input("角色性格（如: 勇敢的战士/狡猾的盗贼/睿智的法师）: ").strip() or "勇敢的冒险者"
    pc_skills_str = input("关键技能（用逗号分隔，如: 剑术,侦查,潜行）: ").strip()
    pc_skills = {}
    if pc_skills_str:
        for skill in pc_skills_str.split(","):
            skill = skill.strip()
            if skill:
                pc_skills[skill] = 60

    pc = CharacterProfile(
        id="pc_main",
        name=pc_name,
        character_type="pc",
        personality=pc_personality,
        skills=pc_skills,
    )

    print("\n选择规则系统：")
    print("  1. 纯叙事模式（推荐）")
    print("  2. CoC 7th 规则")
    print("  3. D&D 5e 规则")
    rules_choice = input("\n> ").strip()
    mechanics = "pure-narrative"
    rules_system = ""
    if rules_choice == "2":
        mechanics = "light-rules"
        rules_system = "coc"
    elif rules_choice == "3":
        mechanics = "light-rules"
        rules_system = "dnd"

    print("\n正在生成初始场景...\n")
    output = engine.new_game(
        name=f"{pc_name}的冒险",
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
    print("━ 输入格式:")
    print('  【对话】        — 角色发言（支持多个【】标记）')
    print("  行动描述         — 角色行动")
    print("  （内心活动）     — 角色内心")
    print("  {继续}           — 采纳判断机制")
    print("  {检定 技能名}    — 执行技能检定")
    print("  {保存}           — 保存游戏")
    print("  {查看在场}       — 查看在场人物")
    print('  {创建NPC 名 描述} — 创建NPC角色卡')
    print('  {导入角色 名称}    — 从 presets/characters/ 导入角色')
    print('  {导入世界观 名称}   — 从 presets/worlds/ 导入世界观')
    print('  {列出角色预设}     — 查看可导入的角色')
    print('  {列出世界观预设}   — 查看可导入的世界观')
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

        response = engine.handle_input(user_input)
        print(f"\n{response}\n")


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
