import sys
import json
import time
import argparse
#from secret_passage_modules import HiddenRoom, HiddenCorridor
#from reach_modules import Gold, Unseen, Horizon
#from general_modules import Pray, Elbereth, Run, Break, Fight, Eat, StairsDescent, StairsAscent, ExploreClosest, RandomWalk
import general_modules
import reach_modules
import secret_passage_modules
from core import GameWhisperer, DungeonWalker, main_logic
from training import BehavioralCloning

def start_bot(create_dataset, filename):
    with open('config.json', 'r') as f:
        config = json.load(f)

    print("\nJudy is looking for the Amulet of Yendor on the map ...\n")
    print("\nVersion: 1.1.9 Stairs\n")

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

    game_interface = GameWhisperer(mode, create_dataset, filename)
    walk_logic = DungeonWalker(game_interface)

    task_prio = config['task_prio_list']
    task_modules_map = {}
    for i in range(0, len(task_prio)):
        task_name = task_prio[i]
        
        if hasattr(general_modules, task_name): task_class = getattr(general_modules, task_name)
        elif hasattr(reach_modules, task_name): task_class = getattr(reach_modules, task_name)
        elif hasattr(secret_passage_modules, task_name): task_class = getattr(secret_passage_modules, task_name)
        else: sys.exit('task not found')

        task_modules_map[task_name] = task_class(walk_logic, game_interface, task_name)
        print(task_name)
        '''
        try:
            task_class = getattr(general_modules, task_name)
        except:
            try:
                task_class = getattr(reach_modules, task_name)
            except:
                try:
                    task_class = getattr(secret_passage_modules, task_name)
                except:
                   raise Exception('task not found')

        '''
        '''
        if task == "pray":
            task_modules_map[task] = Pray(walk_logic, game_interface, task)
        elif task == "take_a_break":
            task_modules_map[task] = Break(walk_logic, game_interface, task)
        elif task == "engrave_elbereth":
            task_modules_map[task] = Elbereth(walk_logic, game_interface, task)
        elif task == "run_for_your_life":
            task_modules_map[task] = Run(walk_logic, game_interface, task)
        elif task == "close_monster_fight":
            task_modules_map[task] = Fight(walk_logic, game_interface, task)
        elif task == "time_of_the_lunch":
            task_modules_map[task] = Eat(walk_logic, game_interface, task)
        elif task == "greed_of_gold":
            task_modules_map[task] = Gold(walk_logic, game_interface, task)
        elif task == "stairs_descent":
            task_modules_map[task] = StairsDescent(walk_logic, game_interface, task)
        elif task == "stairs_ascent":
            task_modules_map[task] = StairsAscent(walk_logic, game_interface, task)
        elif task == "reach_closest_explorable":
            task_modules_map[task] = ExploreClosest(walk_logic, game_interface, task)
        elif task == "reach_horizon":
            task_modules_map[task] = Horizon(walk_logic, game_interface, task)
        elif task == "search_hidden_room":
            task_modules_map[task] = HiddenRoom(walk_logic, game_interface, task)
        elif task == "explore_unseen":
            task_modules_map[task] = Unseen(walk_logic, game_interface, task)
        elif task == "search_hidden_corridor":
            task_modules_map[task] = HiddenCorridor(walk_logic, game_interface, task)
        elif task == "random_walk":
            task_modules_map[task] = RandomWalk(walk_logic, game_interface, task)
        print(task)
        '''
        time.sleep(0.2)

    print("\nJudy is ready for YASD ...")
    print("\n\n")
    time.sleep(1)

    return walk_logic, game_interface, task_prio, task_modules_map, games_number

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--create_dataset',
        dest='create_dataset',
        action='store_true',
        help='Use the bot to generate a dataset of trajectories'
    )
    parser.add_argument(
        '--filename',
        type=str,
        help='The path where to save trajectories' 
    )
    parser.add_argument(
    '--inference',
    dest='training',
    action='store_false',
    help='Use the framework to actually play the game'
    )

    # training parameters
    parser.add_argument(
        '--training',
        dest='training',
        action='store_true',
        help='Train a neural model'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='trajectories',
        help='Path to the dataset for the training process'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Size of the batch in the training process'
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='saved_model',
        help='Path to save the trained model'
    )
    parser.add_argument(
        '--cuda',
        dest='cuda',
        action='store_true',
        help='Use cuda for training'
    )
    parser.add_argument(
        '--no_cuda',
        dest='cuda',
        action='store_false',
        help='Do not use cuda for training'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    parser.add_argument(
        '--learning_rate',
        type=float,
        default=1e-5,
        help='Learning rate of the training process'
    )
    parser.add_argument(
        '--scheduler_gamma',
        type=float,
        default=0.7,
        help='The gamma parameter of the scheduler of the training process'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=5,
        help='Number of epochs'
    )

    flags = parser.parse_args()
    create_dataset = flags.create_dataset
    filename = flags.filename
    training = flags.training
    dataset = flags.dataset
    batch_size = flags.batch_size
    checkpoint = flags.checkpoint

    env_name = 'NetHackChallenge-v0'

    params = {}
    params['use_cuda'] = flags.cuda
    params['seed'] = flags.seed
    params['learning_rate'] = flags.learning_rate
    params['scheduler_gamma'] = flags.scheduler_gamma
    params['epochs'] = flags.epochs

    print(f'training mode: {training}')
    
    if training:
        global training_alg
        training_alg = BehavioralCloning(params, env_name, dataset, batch_size, checkpoint)

        training_alg.train()
    else:
        if create_dataset and not filename:
            sys.exit('no filename to store trajectories')
        dungeon_walker, game, logic, task_map, attempts = start_bot(create_dataset, filename)
        main_logic(dungeon_walker, game, logic, task_map, attempts)

if __name__ == "__main__":
    main()