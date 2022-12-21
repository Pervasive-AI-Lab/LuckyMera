import json
import time
from Judy_Bot_t3.task_modules.secret_passage_modules import HiddenRoom, HiddenCorridor
from Judy_Bot_t3.task_modules.reach_modules import Gold, Unseen, Horizon
from Judy_Bot_t3.task_modules.general_modules import Pray, Elbereth, Run, Break, Fight, Eat, StairsDescent, \
    StairsAscent, ExploreClosest
from Judy_Bot_t3.main import GameWhisperer, DungeonWalker, main_logic


def start_bot():
    with open('config.json', 'r') as f:
        config = json.load(f)

    print("\nJudy is looking for the Amulet of Yendor on the map ...\n")

    exec_mode = config['fast_mode']
    mode = False
    if exec_mode == "on":
        mode = True
        print("\nFast_Mode : ON")
    elif exec_mode == "off":
        print("\nFast_Mode : OFF")
    else:
        print("\nFast_Mode can only be \"on\" or \"off\" -> value set to default : OFF")
    time.sleep(0.5)

    games_number = 100
    try:
        games_number = int(config['attempts'])
        print("Attempts : ", games_number)
    except:
        print("Attempts must be an int value -> value set to default : ", games_number)
        games_number = 100
    time.sleep(0.5)

    game_interface = GameWhisperer(mode)
    walk_logic = DungeonWalker(game_interface)

    task_prio = config['task_prio_list']
    task_map = {}
    for i in range(0, len(task_prio)):
        task = task_prio[i]
        if task == "pray":
            task_map[task] = Pray(walk_logic, game_interface, task)
        elif task == "take_a_break":
            task_map[task] = Break(walk_logic, game_interface, task)
        elif task == "engrave_elbereth":
            task_map[task] = Elbereth(walk_logic, game_interface, task)
        elif task == "run_for_your_life":
            task_map[task] = Run(walk_logic, game_interface, task)
        elif task == "close_monster_fight":
            task_map[task] = Fight(walk_logic, game_interface, task)
        elif task == "time_of_the_lunch":
            task_map[task] = Eat(walk_logic, game_interface, task)
        elif task == "greed_of_gold":
            task_map[task] = Gold(walk_logic, game_interface, task)
        elif task == "stairs_descent":
            task_map[task] = StairsDescent(walk_logic, game_interface, task)
        elif task == "stairs_ascent":
            task_map[task] = StairsAscent(walk_logic, game_interface, task)
        elif task == "reach_closest_explorable":
            task_map[task] = ExploreClosest(walk_logic, game_interface, task)
        elif task == "reach_horizon":
            task_map[task] = Horizon(walk_logic, game_interface, task)
        elif task == "search_hidden_room":
            task_map[task] = HiddenRoom(walk_logic, game_interface, task)
        elif task == "explore_unseen":
            task_map[task] = Unseen(walk_logic, game_interface, task)
        elif task == "search_hidden_corridor":
            task_map[task] = HiddenCorridor(walk_logic, game_interface, task)
        print(task)
        time.sleep(0.4)

    print("\nJudy is ready for YASD ...")
    print("\n\n")
    time.sleep(1)

    return walk_logic, game_interface, task_prio, task_map, games_number


dungeon_walker, game, logic, task_modules_map, attempts = start_bot()

main_logic(dungeon_walker, game, logic, task_modules_map, attempts)
