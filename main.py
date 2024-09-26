import sys
import json
import time
import argparse
import gym
from modules import general_modules, reach_modules, secret_passage_modules, inventory_modules
from core import Saver, GameWhisperer, DungeonWalker, main_logic

def start_bot(env, saver, filename):
    with open('config.json', 'r') as f:
        config = json.load(f)

    print("\nLuckyMera-v1.0 is looking for the Amulet of Yendor on the map ...\n")

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

    game_interface = GameWhisperer(env, mode, saver, filename)
    walk_logic = DungeonWalker(game_interface)

    skill_prio = config['skill_prio_list']
    skill_modules_map = {}
    for i in range(0, len(skill_prio)):
        skill_name = skill_prio[i]
        
        if hasattr(general_modules, skill_name): skill_class = getattr(general_modules, skill_name)
        elif hasattr(reach_modules, skill_name): skill_class = getattr(reach_modules, skill_name)
        elif hasattr(secret_passage_modules, skill_name): skill_class = getattr(secret_passage_modules, skill_name)
        elif hasattr(inventory_modules, skill_name): skill_class = getattr(inventory_modules, skill_name)
        else: sys.exit('skill not found')

        skill_modules_map[skill_name] = skill_class(walk_logic, game_interface, skill_name)
        print(skill_name)
        time.sleep(0.1)

    print("\nLuckyMera-v.10 is ready for YASD ...")
    print("\n\n")
    time.sleep(1)

    return walk_logic, game_interface, skill_prio, skill_modules_map, games_number

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
    '--inference',
    dest='training',
    action='store_false',
    help='Use the framework to actually play the game'
    )
    parser.add_argument(
        '--observation_keys',
        dest='observation_keys',
        nargs='+',
        default=None,
        help='Specify the observation space of nle'
    )
    
    #### DATASET CREATION PARAMETERS ####
    dataset_creation_group = parser.add_argument_group('dataset creation')
    dataset_creation_group.add_argument(
        '--create_dataset',
        dest='create_dataset',
        action='store_true',
        help='Use the bot to generate a dataset of trajectories'
    )
    dataset_creation_group.add_argument(
        '--language_mode',
        dest='language_mode',
        action='store_true',
        help='Save trajectories in language mode, using the nle_language_wrapper'
    )
    dataset_creation_group.add_argument(
        '--keys_to_save',
        dest='keys_to_save',
        nargs='+',
        default=None,
        help='Specify the observation keys to save'
    )
    dataset_creation_group.add_argument(
        '--filename',
        type=str,
        default='saved_trajectories',
        help='The path where to save trajectories' 
    )

    #### TRAINING PARAMETERS ####
    training_group = parser.add_argument_group('training mode')
    training_group.add_argument(
        '--training',
        dest='training',
        action='store_true',
        help='Train a neural model'
    )
    training_group.add_argument(
        '--training_alg',
        type=str,
        default=None,
        help='Select the training algorithm to use'
    )
    training_group.add_argument(
        '--dataset',
        type=str,
        default='saved_trajectories.pkl',
        help='Path to the dataset for the training process'
    )
    training_group.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Size of the batch in the training process'
    )
    training_group.add_argument(
        '--checkpoint',
        type=str,
        default='saved_model',
        help='Path to save the trained model'
    )
    training_group.add_argument(
        '--cuda',
        dest='cuda',
        action='store_true',
        help='Use cuda for training'
    )
    training_group.add_argument(
        '--no_cuda',
        dest='cuda',
        action='store_false',
        help='Do not use cuda for training'
    )
    parser.set_defaults(cuda=True)
    training_group.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    training_group.add_argument(
        '--learning_rate',
        type=float,
        default=1e-5,
        help='Learning rate of the training process'
    )
    training_group.add_argument(
        '--scheduler_gamma',
        type=float,
        default=0.7,
        help='The gamma parameter of the scheduler of the training process'
    )
    training_group.add_argument(
        '--epochs',
        type=int,
        default=5,
        help='Number of epochs'
    )
    parser.set_defaults(training=False)


    flags = parser.parse_args()
    create_dataset = flags.create_dataset
    language_mode = flags.language_mode
    keys_to_save = flags.keys_to_save
    filename = flags.filename
    training_mode = flags.training
    training_alg_name = flags.training_alg
    dataset = flags.dataset
    batch_size = flags.batch_size
    checkpoint = flags.checkpoint
    observation_keys = flags.observation_keys

    training_params = {}
    training_params['use_cuda'] = flags.cuda
    print(f'\n\n\n\nLuckyMera using cuda: {flags.cuda}')
    training_params['seed'] = flags.seed
    training_params['learning_rate'] = flags.learning_rate
    training_params['scheduler_gamma'] = flags.scheduler_gamma
    training_params['epochs'] = flags.epochs

    print(f'training mode: {training_mode}')
    print(f'obs_keys: {observation_keys}')

    env_name = 'NetHackChallenge-v0'
    if observation_keys:
        env = gym.make(env_name, observation_keys=observation_keys)
    #if no observation_keys are specified, all the keys are included
    else: env = gym.make(env_name)
    
    if training_mode:
        import training
        if not training_alg_name:
            raise SystemError('No training algorithm specified')
        if hasattr(training, training_alg_name):
            training_alg_class = getattr(training, training_alg_name)
            print(f'Using {training_alg_name} for training')
        else:
            raise SystemError(f'The training algorithm {training_alg_name} is not implemented in training.py')

        training_alg = training_alg_class(training_params, env, dataset, batch_size, checkpoint)
        training_alg.train()
    else:
        if create_dataset and not filename:
            raise SystemError('no filename to store trajectories')
        if language_mode and not create_dataset:
            raise SystemError('language mode selected, but create_dataset is false')
        if create_dataset and not keys_to_save:
            raise SystemError('keys_to_save equal to None - No keys to save')
       

        if language_mode:
            from nle_language_wrapper import NLELanguageWrapper
            env = NLELanguageWrapper(env, use_language_action=False)
        if create_dataset: saver = Saver(keys_to_save, filename)
        else: saver = None

        dungeon_walker, game, logic, skill_map, attempts = start_bot(env, saver, filename)
        main_logic(dungeon_walker, game, logic, skill_map, attempts)

if __name__ == "__main__":
    main()
