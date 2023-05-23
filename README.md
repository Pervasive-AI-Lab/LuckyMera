# LuckyMera: a Modular AI Framework for Building Hybrid NetHack Agents

## Description

LuckyMera is an integrated framework built around the game of NetHack, one of the oldest and hardest roguelike videogames.
The architecture is designed to build intelligent agents for the game, by constructing high-level game strategies.
LuckyMera is built following the principles of compositionality, modularity and extensibility; this means that the behavior of the agent is determined by a set of *skill* modules, that implement a series of actions to solve specific tasks.
It offers a high-level interface so that it is easy to define and integrate new modules.

LuckyMera leverages the challenging environment offered by NetHack to help AI researchers in designing, integrating and testing new approaches.
It is well-suited to try both symbolic modules and neural ones, giving also the possibility to experiment with hybrid solutions.

LuckyMera comes with three modes of use:
+ *Inference* mode: use the framework agent, with the specified configuration, to play the game. You can also specify which observation the agent is allowed to use:
```
python -m main 
       --inference
       --observation_keys glyphs chars
```
+ *Trajectory saving* mode: save the experiences of the agent in the form of *\<state-action\>* pairs. You have to specify the observation keys you want to save; using the option ```--language_mode```, you can select the text observation given by [```nle_language_wrapper```](https://github.com/Pervasive-AI-Lab/nle-language-wrapper):
```
python -m main
       --create_dataset 
       --keys_to_save glyphs chars
```
+ *Training* mode: use the framework to train a neural model. You can specify the training algorithm and the dataset to use, together with other typical hyperparameters, *e.g.* the learning rate, the batch size and the number of epochs:
```
python -m main --training
       --training_alg BehavioralCloning
       --dataset path/to/dataset --learning_rate 1e-5
       --batch_size 32 --epochs 5
```