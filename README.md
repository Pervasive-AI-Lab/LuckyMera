# Judy_Bot_T3 -- virtually 7th place NetHack agent comparing to [NetHack Challenge at NeurIPS 2021](https://www.aicrowd.com/challenges/neurips-2021-the-nethack-challenge) results

Version: 1.1.7

## Description
Agent Judy_Bot_T3 was developed as a thesis project following the bachelor's degree obtained on 02/12/2022.


Starting from version 1.1.7, the agent is able to obtain an average score of 778 and a median score of 689. Scores acquired by playing the "NetHackChallenge-v0" task through the
[NetHack Learning Environment](https://github.com/facebookresearch/nle) framework.

The code is completely open-source and has been designed with the aim of complying with the principles of configurability, 
modularity and extensibility. It is in fact possible to extend the agent through the implementation of modules dedicated to the planning and execution of new tasks.


## Environment
All Judy_Bot_T3 software dependencies are limited to the [NLE](https://github.com/facebookresearch/nle) installation.

The version of [NLE](https://github.com/facebookresearch/nle) used in the programming phase is 0.8.1.
Other software dependencies are closely related to the requirements for installing [NLE](https://github.com/facebookresearch/nle).



## How to run

To run the agent, simply use the shell command `python -m main` to start the code flow.

Thanks to the `config.json` configuration file it is possible to determine some aspects of the behavior of the software and the agent:

* The `task_prio_list` key allows you to define a list of tasks in order of priority (with their symbolic names).
The agent will consider the order given as a trace to administer his own logic, reserving the right to dynamically modify the established priorities in relation to the different game situations.
Currently, the agent has the ability to plan and execute 14 different tasks, which find their implementation in specific Python classes (see next section).
Below is a list of the symbolic names of the tasks accompanied by a brief description of their behavior. This specific order corresponds to the strategy that led Judy_Bot_T3 to the previously stated results:

  * `pray` -> Where the agent's prayer is planned, considering the requirements for safe prayer and the agent's needs,
  
  * `engrave_elbereth` -> Which allows the agent to engrave Elbereth on the ground, thus defending himself from some malevolent creatures,
  
  * `run_for_your_life` -> Which allows the agent to escape from unpleasant situations, fleeing from danger,
  
  * `take_a_break` -> Which allows the agent to rest and restore their vitality,
  
  * `close_monster_fight` -> 
Which allows the agent to fight, employing a strategy of avoiding passive monsters and not granting enemies bonus attacks,
  
  * `time_of_the_lunch` -> 
Which allows the agent to feed, avoiding eating dangerous food and checking for the presence of traps in suspicious corpses,
  
  * `greed_of_gold` -> Which allows the agent to reach and collect gold during his adventure,
  
  * `stairs_descent` -> Which allows the agent to descend into the dungeon according to a "slow descent" logic,
  
  * `stairs_ascent` -> Which allows the agent to go back up in the dungeon according to a "slow descent" logic,
  
  * `reach_closest_explorable` -> Which allows the agent to reach and interact with points of interest for exploration, such as doors and corridors,
  
  * `reach_horizon` -> Which allows the agent to reach the frontier of exploration, expanding their knowledge of the dungeon,
  
  * `explore_unseen` -> Which allows the agent to reach tiles they have never walked on,
  
  * `search_hidden_room` -> Which allows the agent to locate secret passages in dungeon rooms,
  
  * `search_hidden_corridor` -> Which allows the agent to locate secret passages in dungeon corridors.

    
* The `fast_mode` key determines how the agent will run. When the configured value is `on`, Judy_Bot_T3 will play NetHack without the terminal showing the game interface, saving computational resources for the massive execution of several games, printing a simple agent performance report.
When the configured value is `off`, the games played by Judy_Bot_T3 will be viewable through the typical game interface.


* The `attempts` key determines the number of games the agent will play.




## Code structure

The entire agent's logic is based on the modules that implement its tasks. Therefore, in order to expand the capabilities of the agent, it is necessary to extend the `Task` class or one of the other classes below it in the hierarchy, implementing the `planning()` and `execution()` methods, allowing the bot to integrate the task within its logic.

The following is a brief description of the main structural components of Judy_Bot_T3:

* `config.json` is the previously discussed configuration file,
* `main.py` is the startup component of the agent. Its code allows the parsing of the configuration file and the setting in motion of the whole logic of Judy_Bot-T3,
* `core.py` is the central component in interacting with the NLE framework and the underlying NetHack game,
* `archetype_modules.py` encompasses the three archetype classes for task definition: `Task` (the most general model), `ReachTask` (specialized in tasks that require to reach a specific glyph without too many frills) and `HiddenTask` (specialized in finding hidden areas),
* `reach_modules.py` includes classes that define tasks related to the `ReachTask` archetype,
* `secret_passage_modules.py` includes classes that define tasks related to the `HiddenTask` archetype,
* `general_modules.py` includes classes that define tasks related to the `Task` archetype, These are generic tasks and therefore not currently attributable to a more specific archetype.

