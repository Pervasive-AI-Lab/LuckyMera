from modules.archetype_modules import Skill
import random
import numpy as np

class BCWalk(Skill):
   def __init__(self, dungeon_walker, game, skill_name):
        from stable_baselines3 import A2C
        super().__init__(dungeon_walker, game, skill_name)
        self.model = A2C.load('bc_model.zip')
        
    #behavioral cloning agent can be always used
    def planning(self, stats, safe_play, agent):
        return self.name, None, None

    def execution(self, path, arg1, agent, stats):
        #format the obs as in training
        a2c_obs =  np.concatenate((self.game.current_obs['chars'], self.game.current_obs['colors']), axis=None)
        action, _ = self.model.predict(a2c_obs)
        rew, done, info = self.game.do_it(action, None)
        return rew, done, info

class NeuralWalk(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        from minihack.agent.polybeast.evaluate import load_model, get_action
        super().__init__(dungeon_walker, game, skill_name)
        self.model, self.hidden = load_model('challenge', '/home/lquarantiello/minihack/minihack/agent/polybeast/outputs/Room-Ultimate-15x15_IMPALA_2e7')

    #using the rl model to walk is always possible
    def planning(self, stats, safe_play, agent):
        return self.name, None, None
    
    def execution(self, path, arg1, agent, stats):
        action, self.hidden = get_action(self.model, self.game.current_obs, self.hidden, done=False, watch=False)
        print(f"Action selected: {action}")
        rew, done, info = self.game.do_it(action, None)
        return rew, done, info

class RandomWalk(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)
        self.counter = 0

    #random walking is always applicable
    def planning(self, stats, safe_play, agent):
        return self.name, None, None

    def execution(self, path, arg1, agent, stats):
        #movement action are from id 0 to 7 included
        move_action = random.randint(0,7)
        print(f"Movement action selected: {move_action}")
        rew, done, info = self.game.do_it(move_action, None)
        self.counter += 1
        print(f'RandomWalk counter: {self.counter}')
        return rew, done, info


class StairsDescent(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def planning(self, stats, safe_play, agent):
        """
             function for skill planning

             :param safe_play: flag identifying the need for a safe play
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return name -> a string containing skill name
                     path -> a list containing the actions to be performed to reach a certain possible target
                     arg1 -> extra optional output (target's coordinates in this case)
         """

        if not self.custom_contain(self.game.get_stairs_locations()[0], stats[12])[0]:
            found, y, x = self.game.find(self.standard_condition, [60])
            if found:
                self.game.append_stairs_location((stats[12], y, x), True)  # 1.1.9

        if not self.custom_contain(self.game.get_stairs_locations()[1], stats[12])[0]:
            found, y, x = self.game.find(self.standard_condition, [62])
            if found:
                self.game.append_stairs_location((stats[12], y, x), False)  # 1.1.9

        if (not 2 <= stats[21] <= 4 or self.game.get_depth_turns(stats[12]) < 500) or stats[18] + 1 <= stats[12]:
            # and not self.bl_stats[18] >= self.bl_stats[12] + 3: v2.0
            return None, None, None

        known, coords = self.custom_contain(self.game.get_stairs_locations()[1], stats[12])

        if not known:
            path, coords = self.standard_plan([(62, 7)], False, False)
        else:
            path = self.dungeon_walker.path_finder(coords[0], coords[1], False, False)
            self.game.update_memory(coords[0], coords[1])
        if path is None:
            return None, None, None
        else:
            return self.name, path, coords

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        rew, done, info = self.do_plan(path)
        if rew == -1:
            self.game.clear_memory(arg1[0], arg1[1])
            return rew, done, info
        agent = self.game.get_agent_position()
        if not done and agent[0] == arg1[0] and agent[1] == arg1[1]:
            rew, done, info = self.game.do_it(17, None)  # go down
            agent = self.game.get_agent_position()
            self.game.partial_reset_game()
            self.game.reset_hard_search_num()  # ricorda
            if self.game.update_agent():
                self.game.update_memory(agent[0], agent[1])
        return rew, done, info


class StairsAscent(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def planning(self, stats, safe_play, agent):
        """
             function for skill planning

             :param safe_play: flag identifying the need for a safe play
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return name -> a string containing skill name
                     path -> a list containing the actions to be performed to reach a certain possible target
                     arg1 -> extra optional output (target's coordinates in this case)
         """

        if stats[12] == 1 or 2 <= stats[21] <= 4:  # or stats[18] >= stats[12] + 3:  # or self.bl_stats[18] >= self.bl_stats[12] + 3:
            return None, None, None
        known, coords = self.custom_contain(self.game.get_stairs_locations()[0], stats[12])
        if not known:
            path, coords = self.standard_plan([(60, 7)], False, False)
        else:
            path = self.dungeon_walker.path_finder(coords[0], coords[1], False, False)
            self.game.update_memory(coords[0], coords[1])
        if path is None:
            return None, None, None
        else:
            return self.name, path, coords

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        rew, done, info = self.do_plan(path)
        if rew == -1:
            self.game.clear_memory(arg1[0], arg1[1])
            return rew, done, info
        agent = self.game.get_agent_position()
        if not done and agent[0] == arg1[0] and agent[1] == arg1[1]:
            rew, done, info = self.game.do_it(16, None)  # go up
            agent = self.game.get_agent_position()
            self.game.partial_reset_game()
            self.game.reset_hard_search_num()  # ricorda
            if self.game.update_agent():
                self.game.update_memory(agent[0], agent[1])
        return rew, done, info


class Pray(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def planning(self, stats, safe_play, agent):
        """
             function for skill planning

             :param safe_play: flag identifying the need for a safe play
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return name -> a string containing skill name
                     path -> a list containing the actions to be performed to reach a certain possible target (None)
                     arg1 -> extra optional output (None)
         """

        if (stats[21] == 4 or stats[10] <= 6 or (
                stats[11] != 0 and (stats[10] / stats[11]) < 0.14)) and (
                abs(self.game.get_last_pray() - stats[20]) >= 500 or self.game.get_last_pray() == -1) and stats[
             20] > 100:
            return self.name, None, None

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        if self.game.update_agent():
            rew, done, info = self.game.do_it(62, None)  # pray
            self.game.update_last_pray()
        else:
            rew = 0
            done = True
            info = None
        return rew, done, info


class Elbereth(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def planning(self, stats, safe_play, agent):
        """
             function for skill planning

             :param safe_play: flag identifying the need for a safe play
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return name -> a string containing skill name
                     path -> a list containing the actions to be performed to reach a certain possible target (None)
                     arg1 -> extra optional output (None)
         """

        if abs(self.game.get_elbereth_violation() - stats[20]) < 7 or stats[21] == 4:
            return None, None, None  # 1.1.8.6
        for tile in self.game.neighbors_8_dir(agent[0], agent[1]):
            char = self.game.get_char(tile[0], tile[1])
            color = self.game.get_color(tile[0], tile[1])
            # (char == 66 and color == 1)
            if char == 65 or (char == 104 and (color == 1 or color == 3)) or char == 64:
                return None, None, None  # 1.1.8.2

        # not self.game.check_engraved(agent) and
        if self.game.get_risk(agent[0], agent[1]) > 4 or (stats[11] != 0 and (stats[10] / stats[11]) < 0.75):
            return self.name, None, None

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        rew, done, info = self.game.do_it(36, None)  # engrave
        self.game.append_engraved((agent[0], agent[1]))

        # 1.1.8.3
        if not self.game.get_parsed_message().__contains__("flee"):
            return rew, done, info

        # w_count = 0
        # risk = self.game.get_risk(agent[0], agent[1])
        # ((stats[11] != 0 and (stats[10] / stats[11]) < 0.8) or risk > 2)
        while (stats[11] != 0 and (stats[10] / stats[11]) < 0.9) \
                and not done and stats[21] < 4:  # and not (w_count > 1 and risk >= 2):
            rew, done, info = self.game.do_it(75, None)  # wait - with search
            if not self.game.get_fast_mode():
                print("\nElbereth WAIT ---\n")
            # risk = self.game.get_risk(agent[0], agent[1])
            # w_count += 1
            stats = self.game.get_bl_stats()
            message = self.game.get_parsed_message()
            if message.__contains__("hit") or \
                    message.__contains__("bite") or \
                    message.__contains__("attack") or \
                    message.__contains__("throw") or \
                    message.__contains__("swing") or \
                    message.__contains__("thrusts"):
                self.game.set_elbereth_violation()
                break
        return rew, done, info


class Run(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def planning(self, stats, safe_play, agent):
        """
             function for skill planning

             :param safe_play: flag identifying the need for a safe play
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return name -> a string containing skill name
                     path -> a list containing the actions to be performed to reach a certain possible target (None)
                     arg1 -> extra optional output (the best tile to run to in this case)
         """

        for tile in self.game.neighbors_8_dir(agent[0], agent[1]):
            char = self.game.get_char(tile[0], tile[1])
            color = self.game.get_color(tile[0], tile[1])
            if (char == 100 and color == 1) or \
                    (char == 117 and not self.game.get_pet_alive()) or \
                    ((char == 102 or char == 100) and (
                            color == 7 or color == 15) and not self.game.get_pet_alive()) or \
                    (char == 64 and (color == 1 or color == 3)) or \
                    (char == 97) or \
                    (char == 66):
                return None, None, None  # 1.1.8.2

        risk = self.game.get_risk(agent[0], agent[1])
        # risk < 1 or risk > 3 or \
        if risk < 1 or (stats[11] != 0 and (stats[10] / stats[11]) > 0.50) or self.game.get_ran():
            return None, None, None
        else:
            if self.game.is_doorway(agent[0], agent[1]):
                around_me = self.game.neighbors_4_dir(agent[0], agent[1])
            else:
                around_me = self.game.neighbors_8_dir(agent[0], agent[1])
            champion = agent
            found = False
            for tile in around_me:
                risk_c = self.game.get_risk(champion[0], champion[1])
                risk_t = self.game.get_risk(tile[0], tile[1])
                char = self.game.get_char(tile[0], tile[1])
                if risk_c > risk_t and self.game.is_walkable(tile[0], tile[1]) and \
                        char != 100 and \
                        char != 102 and \
                        char != 117 and \
                        char != 96:

                    if not (self.game.is_doorway(tile[0], tile[1]) and agent[0] != tile[0] and agent[1] !=
                            tile[1]):
                        if abs(self.game.get_memory(tile[0], tile[1]) - self.game.get_act_num()) > 2:
                            champion = tile
                            found = True
            if found:
                return self.name, None, champion
            else:
                return None, None, None

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        rew, done, info = self.game.do_it(
            self.game.move_translator(agent[0], agent[1], arg1[0], arg1[1]),
            None)
        message = self.game.get_parsed_message()
        if (message.__contains__("fox") or
            message.__contains__("dog") or
            message.__contains__("pony") or
            message.__contains__("kitten") or
            message.__contains__("ant") or
            message.__contains__("throw") or
            message.__contains__("bat") or
            message.__contains__("bee")) and \
                not message.__contains__("swap"):
            self.game.update_ran()
        else:
            self.game.reset_ran()
        return rew, done, info


class ExploreClosest(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        self.chosen_skill = None
        super().__init__(dungeon_walker, game, skill_name)

    # metodo ausiliario per la ricerca e il pathfinding verso la casella adiacente ad un gruppo di obbiettivi
    def mixed_plan(self, glyphs, condition, safe_play):
        """
            function for finding a path to a tile given a set of possible objective

            :param glyphs: set of possible objective tiles
            :param condition: condition function to be applied
            :param safe_play: flag identifying the need for a safe play
            :return path to and position of a found tile
        """

        path = None
        found, y, x = self.game.find(condition, glyphs)
        if found:
            char = self.game.get_char(y, x)
            color = self.game.get_color(y, x)
            if char == 43 and color == 3:
                ny = -1
                nx = -1
                near = self.game.neighbors_4_dir(y, x)
                while len(near) > 0:
                    next_tile = near.pop()
                    if self.game.is_walkable(next_tile[0], next_tile[1]):
                        ny = next_tile[0]
                        nx = next_tile[1]
                        break
                path = self.dungeon_walker.path_finder(ny, nx, False, safe_play)
            elif char == 35:
                path = self.dungeon_walker.path_finder(y, x, False, safe_play)
            else:
                path = self.dungeon_walker.path_finder(y, x, True, safe_play)
        self.game.update_memory(y, x)
        return path, (y, x)

    def condition_multiple_obj_v0(self, tile, args):
        """
            condition function for identifying a tile according to a list of possible tiles

            :param tile: tile to test
            :param args: arguments for the given condition (list of correct tiles combinations)
            :return TRUE -> if condition is verified, FALSE -> elsewise
        """

        if args.__contains__((self.game.get_char(tile[0], tile[1]), self.game.get_color(tile[0], tile[1]))) and \
                (self.game.get_memory(tile[0], tile[1]) == -1 or
                 (not self.game.get_char(tile[0], tile[1]) == 35 and abs(
                     self.game.get_memory(tile[0], tile[1]) - self.game.get_act_num()) >
                  self.game.glyph_cooldown(
                      (self.game.get_char(tile[0], tile[1]), self.game.get_color(tile[0], tile[1]))))) \
                and (not self.game.get_char(tile[0], tile[1]) == 46 or self.game.is_doorway(tile[0], tile[1])):
            return True
        else:
            return False

    def sort_key_func(self, tile):
        """
            function that calculates a sorting parameter for the elements of a list
            according to how many neighboring tiles carry the same glyph

            :param  tile: the given tile
            :return the opposite in sign of the count made
        """

        tile_nbh = self.game.neighbors_8_dir(tile[0], tile[1])
        glyph = self.game.get_glyph(tile[0], tile[1])
        count = 0
        for i in tile_nbh:
            if self.game.get_glyph(i[0], i[1]) == glyph:
                count += 1
        return -count

    # metodo che se possibile sposta l'agente nella casella adiacente con/senza(equal) il glifo corrispondente
    def roam_to_next_glyph(self, glyph, equal):
        """
            function that move the agent to a neithboring tile
            containing (or not containing, depending on "equal" value)
            a given glyph

            :param  glyph: the given glyph
            :param  equal: flag that switches between two opposite behaviours of the function
            :return: 0 -> if there aren't neighboring tiles according to the need, 1 -> elsewise
                     the "reward" value (1 if episode success, 0 elsewise),
                     the "done" value (TRUE if the episode endend, FALSE elsewise),
                     the "info" object containg extra information (Gym standard implementation)
        """

        char = glyph[0]
        color = glyph[1]
        rew = 0
        done = False
        info = None

        agent = self.game.get_agent_position()
        near = self.game.neighbors_4_dir(agent[0], agent[1])
        near.sort(key=self.sort_key_func)

        dummy = self.game.neighbors_8_dir(agent[0], agent[1])
        for i in near:
            dummy.remove(i)
        dummy.sort(key=self.sort_key_func)

        near.extend(dummy)

        while len(near) > 0:
            next_tile = near.pop(0)
            char_n = self.game.get_char(next_tile[0], next_tile[1])
            color_n = self.game.get_char(next_tile[0], next_tile[1])
            if self.game.is_unexplored(next_tile[0], next_tile[1]) and (glyph is None or
                                                                        (not equal and (char_n, color_n) != (
                                                                                char, color)) or
                                                                        (equal and (char_n, color_n) == (
                                                                                char, color)) or
                                                                        char_n == 96 or
                                                                        char_n == 37 or
                                                                        char_n == 36) \
                    and self.game.is_walkable(next_tile[0], next_tile[1]):
                agent = self.game.get_agent_position()
                rew, done, info = self.game.do_it(
                    self.game.move_translator(agent[0], agent[1], next_tile[0], next_tile[1]), None)
                if self.game.update_agent():
                    message = self.game.get_parsed_message()
                    if message.__contains__("It's solid stone.") or \
                            message.__contains__("It's a wall.") or \
                            message.__contains__("You can't move diagonally into an intact doorway.") or \
                            message.__contains__("You try to move the boulder, but in vain.") or \
                            message.__contains__("Perhaps that's why you cannot move it.") or \
                            message.__contains__("You hear a monster behind the boulder."):
                        self.game.append_exception(next_tile)
                        return 0, rew, done, info
                    return 1, rew, done, info
        return 0, rew, done, info

    # metodo per seguire un percorso di glifi '#'(corridoio) ignoti fino ad esaurirli
    def corridor_roamer(self):
        """
            function that move the agent across a corridor on the map, stopping at
            the end of a corridor's branch

            :return: TRUE -> if the roaming endend well, 1 -> elsewise
                     the "reward" value (1 if episode success, 0 elsewise),
                     the "done" value (TRUE if the episode endend, FALSE elsewise),
        """

        last_roam = 1
        done = False
        rew = 0
        while last_roam == 1 and not self.eject_button():
            last_roam, rew, done, info = self.roam_to_next_glyph((35, 7), True)

        # se il corridoio è terminato regolarmente
        if last_roam == 0:
            # se non è presente un'uscita esegui 'search' 20 volte
            last_roam, rew, done, info = self.roam_to_next_glyph((35, 7), False)
            i = 0
            agent = self.game.get_agent_position()
            while last_roam == 0 and i < 30 and not done and not self.game.get_parsed_message().__contains__("You find") \
                    and not self.game.unexplored_walkable_around(agent[0], agent[1]) \
                    and not 3 <= self.game.get_bl_stats()[21] <= 4:

                if not self.game.update_agent():
                    return False, rew, True
                if self.eject_button():
                    return False, rew, done
                if not self.game.get_fast_mode():
                    print("search in suspect corridor end... try:", i)
                rew, done, info = self.game.do_it(75, None)  # search
                i += 1
                # prova a spostarsi in una casella '#' appena scoperta
                if not done:
                    last_roam, rew, done, info = self.roam_to_next_glyph((35, 7), True)
                if last_roam != 1 and not done:
                    # se non riesce effettua due passi in caselle adiacenti ignote
                    last_roam, rew, done, info = self.roam_to_next_glyph((35, 7), False)
                    if done:
                        break
                    last_roam, rew, done, info = self.roam_to_next_glyph((35, 7), False)
                else:
                    # se riesce dovrà seguire anche il nuovo corridoio appena individuato
                    break
                agent = self.game.get_agent_position()
        else:
            return False, rew, done

        return True, rew, done

    def planning(self, stats, safe_play, agent):
        """
               function for skill planning

               :param safe_play: flag identifying the need for a safe play
               :param agent: actual agent position according to agent's knowledge
               :param stats: actual in-game character's stats according to agent's knowledge
               :return name -> a string containing skill name
                       path -> a list containing the actions to be performed to reach a certain possible target
                       arg1 -> extra optional output (target's coordinates in this case)
        """

        path, coords = self.mixed_plan([(35, 15), (35, 7), (46, 7), (45, 3), (124, 3), (43, 3)],
                                       self.condition_multiple_obj_v0, safe_play)
        if path is None or len(path) == 0:
            return None, None, None
        else:
            char = self.game.get_char(coords[0], coords[1])
            color = self.game.get_color(coords[0], coords[1])
            if char == 43 and color == 3:
                self.chosen_skill = "reach_doorway_closed"
                return "reach_doorway_closed", path, coords
            elif char == 35:
                self.chosen_skill = "corridor_roam"
                return "corridor_roam", path, coords
            else:
                self.chosen_skill = "reach_doorway_open"
                return "reach_doorway_open", path, coords

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        if self.chosen_skill == "reach_doorway_open":
            rew, done, info = self.do_plan(path)
            if rew == -1:
                self.game.clear_memory(arg1[0], arg1[1])
                return rew, done, info
            j = 0
            while self.game.is_near_glyph(agent[0], agent[1], (32, 0),
                                          4) and not self.eject_button() and j < 40 and not done and not self.game.get_parsed_message().__contains__(
                 "You find"):  # when near void

                if 3 <= stats[21] <= 4:
                    break

                if not self.game.get_fast_mode():
                    print("searching on the void... try: ", j)
                rew, done, info = self.game.do_it(75, None)  # search
                agent = self.game.get_agent_position()
                stats = self.game.get_bl_stats()
                j += 1
            return rew, done, info

        elif self.chosen_skill == "reach_doorway_closed":
            rew, done, info = self.do_plan(path)
            if self.game.get_parsed_message().__contains__(" no door"):
                # self.game.append_exception((arg1[0], arg1[1]))
                return rew, done, info
            if rew == -1:
                self.game.clear_memory(arg1[0], arg1[1])
                return rew, done, info
            if self.game.get_parsed_message().__contains__("Something is written here in the dust."):
                self.game.append_exception((arg1[0], arg1[1]))
                return rew, done, info
            if not done and rew != -1 and not self.game.get_parsed_message().__contains__(
                    "This door is already open.") and not self.game.get_parsed_message().__contains__("inventory"):
                door_direction = self.game.move_translator(agent[0], agent[1], arg1[0], arg1[1])
                rew, done, info = self.game.do_it(57, door_direction)  # open
                while not done and not self.eject_button() and self.game.get_parsed_message().__contains__(
                        "This door is locked.") or self.game.get_parsed_message().__contains__("WHAMMM!!!") \
                        or self.game.get_parsed_message().__contains__("The door resists!"):
                    rew, done, info = self.game.do_it(48, door_direction)  # kick
                self.game.clear_memory(arg1[0], arg1[1])
            return rew, done, info

        elif self.chosen_skill == "corridor_roam":
            rew, done, info = self.do_plan(path)
            if rew == -1:
                self.game.clear_memory(arg1[0], arg1[1])
                return rew, done, info
            if not done and rew != -1:
                out = self.corridor_roamer()
                rew = out[1]
                done = out[2]

            return rew, done, info


class Fight(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    @staticmethod
    def condition_close_obj(tile, args):
        """
            condition function for identifying a tile which verifies a certain condition in a given area

            :param tile: tile to test
            :param args: arguments for the given condition
                         (an auxiliar condition function, a range and a center origin point)
            :return TRUE -> if condition is verified, FALSE -> elsewise
        """

        condition = args[0]
        look_range = args[1]
        center = args[2]
        if abs(tile[0] - center[0]) <= look_range and abs(tile[1] - center[1]) <= look_range:
            if condition(tile[0], tile[1]):
                return True
        return False

    # metodo ausiliario per la ricerca e il pathfinding verso un gruppo di obbiettivi in un range limitato
    def close_plan(self, not_reach_diag, condition, look_range, safe_play):
        """
            function for finding a path to a tile given a set of possible objective

            :param not_reach_diag: flag identifying a tile which cant be reachen diagonally
            :param condition: condition function to be applied
            :param look_range: a certain range for target's research
            :param safe_play: flag identifying the need for a safe play
            :return path to and position of a found tile
        """

        path = None
        # y = -1
        # x = -1
        agent = self.game.get_agent_position()
        found, y, x = self.game.find(self.condition_close_obj, [condition, look_range, agent])
        if found:
            char = self.game.get_char(y, x)
            color = self.game.get_color(y, x)
            if not self.game.get_fast_mode():
                print("monster info -> char: ", char, " - color: ", color)
            if self.game.get_parsed_message().__contains__("statue"):
                self.game.append_monster_exception((y, x))
            lms = self.game.get_last_monster_searched()
            if lms[0] == char and lms[1] == \
                    color:
                self.game.update_last_monster_searched(char, color, lms[2] + 1)
                if lms[2] > 12:  # probabile statua
                    self.game.monster_exception.append((y, x))
            else:
                self.game.update_last_monster_searched(char, color, 1)

            agent = self.game.get_agent_position()
            if abs(agent[0] - y) <= 1 and (agent[1] - x) <= 1:
                return [], (y, x)
            ny = -1
            nx = -1
            near = self.game.neighbors_8_dir(y, x)
            while len(near) > 0:
                next_tile = near.pop()
                if self.game.is_walkable(next_tile[0], next_tile[1]):
                    ny = next_tile[0]
                    nx = next_tile[1]
                    break
            path = self.dungeon_walker.path_finder(ny, nx, not_reach_diag, safe_play)
            self.game.update_memory(y, x)
        return path, (y, x)

    def planning(self, stats, safe_play, agent):
        """
               function for skill planning

               :param safe_play: flag identifying the need for a safe play
               :param agent: actual agent position according to agent's knowledge
               :param stats: actual in-game character's stats according to agent's knowledge
               :return name -> a string containing skill name
                       path -> a list containing the actions to be performed to reach a certain possible target
                       arg1 -> extra optional output (target's coordinates in this case)
        """

        path, coords = self.close_plan(False, self.game.is_a_monster, 5, False)
        if path is None:
            return None, None, None
        else:
            return self.name, path, coords

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        length = len(path)
        y_dist = abs(arg1[0] - agent[0])
        x_dist = abs(arg1[1] - agent[1])
        rew = 0
        done = False
        info = None
        if y_dist >= 3 and x_dist >= 5 and length > 0 and not done:
            if self.game.update_agent():
                direction = path.pop()
                next_tile = self.game.inverse_move_translator(agent[0], agent[1], direction)
                if not self.game.is_passive_monster(next_tile[0], next_tile[1]):
                    rew, done, info = self.game.do_it(direction, None)
            else:
                return 0, True, None
        elif y_dist == 2 or x_dist == 2 and not done:
            rew, done, info = self.game.do_it(75, None)  # Wait - searching
        elif not done:
            direction = self.game.move_translator(agent[0], agent[1], arg1[0], arg1[1])
            self.game.do_it(direction, None)  # attack

            message = self.game.get_parsed_message()
            act = self.game.get_act_num()
            if message.__contains__("kill") and not message.__contains__("zombie"):  # mostri rimossi: dwarf
                if message.__contains__("goblin"):
                    self.game.append_recently_killed(("goblin", act, arg1[0], arg1[1]))
                elif message.__contains__("fox"):
                    self.game.append_recently_killed(("fox", act, arg1[0], arg1[1]))
                elif message.__contains__("rat"):
                    self.game.append_recently_killed(("rat", act, arg1[0], arg1[1]))
                elif message.__contains__("newt"):
                    self.game.append_recently_killed(("newt", act, arg1[0], arg1[1]))
                elif message.__contains__("jackal"):
                    self.game.append_recently_killed(("jackal", act, arg1[0], arg1[1]))
                elif message.__contains__("shrieker"):
                    self.game.append_recently_killed(("shrieker", act, arg1[0], arg1[1]))
                elif message.__contains__("hobbit"):
                    self.game.append_recently_killed(("hobbit", act, arg1[0], arg1[1]))
                elif message.__contains__("red mold"):
                    self.game.append_recently_killed(("red mold", act, arg1[0], arg1[1]))
                elif message.__contains__("green mold"):
                    self.game.append_recently_killed(("green mold", act, arg1[0], arg1[1]))
                elif message.__contains__("brown mold"):
                    self.game.append_recently_killed(("brown mold", act, arg1[0], arg1[1]))
                elif message.__contains__("acid blob"):
                    self.game.append_recently_killed(("acid blob", act, arg1[0], arg1[1]))
                elif message.__contains__("gecko"):
                    self.game.append_recently_killed(("gecko", act, arg1[0], arg1[1]))
                elif message.__contains__("coyote"):
                    self.game.append_recently_killed(("coyote", act, arg1[0], arg1[1]))
                elif message.__contains__("human"):  # new
                    self.game.append_recently_killed(("human", act, arg1[0], arg1[1]))
                elif message.__contains__("dog"):
                    self.game.append_recently_killed(("dog", act, arg1[0], arg1[1]))
                elif message.__contains__("kitten"):
                    self.game.append_recently_killed(("kitten", act, arg1[0], arg1[1]))
                elif message.__contains__("iguana"):
                    self.game.append_recently_killed(("iguana", act, arg1[0], arg1[1]))
                elif message.__contains__("floating eye"):
                    self.game.append_recently_killed(("floating eye", act, arg1[0], arg1[1]))
                elif message.__contains__("orc"):
                    self.game.append_recently_killed(("orc", act, arg1[0], arg1[1]))
                elif message.__contains__("Keystone Kop"):
                    self.game.append_recently_killed(("Keystone Kop", act, arg1[0], arg1[1]))
                elif message.__contains__("hobgoblin"):
                    self.game.append_recently_killed(("hobgoblin", act, arg1[0], arg1[1]))
                elif message.__contains__("gnome"):
                    self.game.append_recently_killed(("gnome", act, arg1[0], arg1[1]))
                elif message.__contains__("garter snake"):
                    self.game.append_recently_killed(("garter snake", act, arg1[0], arg1[1]))
                elif message.__contains__("cave spider"):
                    self.game.append_recently_killed(("cave spider", act, arg1[0], arg1[1]))
                elif message.__contains__("leprechaun"):
                    self.game.append_recently_killed(("leprechaun", act, arg1[0], arg1[1]))
                elif message.__contains__("woodchuck"):
                    self.game.append_recently_killed(("woodchuck", act, arg1[0], arg1[1]))
                elif message.__contains__("mole"):
                    self.game.append_recently_killed(("mole", act, arg1[0], arg1[1]))
                elif message.__contains__("imp"):  # new
                    self.game.append_recently_killed(("imp", act, arg1[0], arg1[1]))
                elif message.__contains__("pony"):
                    self.game.append_recently_killed(("pony", act, arg1[0], arg1[1]))
                elif message.__contains__("piercer"):
                    self.game.append_recently_killed(("piercer", act, arg1[0], arg1[1]))
                elif message.__contains__("naga hatchling"):
                    self.game.append_recently_killed(("naga hatchling", act, arg1[0], arg1[1]))
                elif message.__contains__("crocodile"):
                    self.game.append_recently_killed(("crocodile", act, arg1[0], arg1[1]))
                elif message.__contains__("dwarf"):  # new
                    self.game.append_recently_killed(("dwarf", act, arg1[0], arg1[1]))
                elif message.__contains__("centipede"):
                    self.game.append_recently_killed(("centipede", act, arg1[0], arg1[1]))
                elif message.__contains__("monkey"):
                    self.game.append_recently_killed(("monkey", act, arg1[0], arg1[1]))
                elif message.__contains__("blue jelly"):
                    self.game.append_recently_killed(("blue jelly", act, arg1[0], arg1[1]))
                elif message.__contains__("housecat"):
                    self.game.append_recently_killed(("housecat", act, arg1[0], arg1[1]))
                elif message.__contains__("dingo"):
                    self.game.append_recently_killed(("dingo", act, arg1[0], arg1[1]))
                elif message.__contains__("Uruk-hai"):
                    self.game.append_recently_killed(("Uruk-hai", act, arg1[0], arg1[1]))
                elif message.__contains__("bugbear"):
                    self.game.append_recently_killed(("bugbear", act, arg1[0], arg1[1]))
                elif message.__contains__("naga"):
                    self.game.append_recently_killed(("naga", act, arg1[0], arg1[1]))
                elif message.__contains__("rothe"):
                    self.game.append_recently_killed(("rothe", act, arg1[0], arg1[1]))
                elif message.__contains__("ant"):
                    self.game.append_recently_killed(("ant", act, arg1[0], arg1[1]))
                elif message.__contains__("gray ooze"):
                    self.game.append_recently_killed(("gray ooze", act, arg1[0], arg1[1]))

        return rew, done, info


class Eat(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def fresh_food(self):
        """
            function for safe to eat food identification (only for corpses of monsters killed by the agent)
            according to agent memory and turns passed

            :return TRUE -> if the screen displays a safe food, FALSE -> elsewise
        """
        # message = self.game.get_parsed_message()
        message = self.game.parse_all()
        stats = self.game.get_bl_stats()

        if (message.__contains__("gray ooze") or message.__contains__("acid blob") or message.__contains__("green mold") or message.__contains__("black naga")) and stats[10] < 20:
            return False

        agent = self.game.get_agent_position()
        for log in self.game.get_recently_killed():
            monster = log[0]
            turn = log[1]
            if abs(turn - self.game.get_act_num()) > 30:
                self.game.remove_recently_killed(log)
            elif message.__contains__(monster) and \
                    abs(agent[0] - log[2]) <= 2 and abs(agent[1] - log[3]) <= 2:
                self.game.remove_recently_killed(log)
                return True
        return False

    def planning(self, stats, safe_play, agent):
        """
               function for skill planning

               :param safe_play: flag identifying the need for a safe play
               :param agent: actual agent position according to agent's knowledge
               :param stats: actual in-game character's stats according to agent's knowledge
               :return name -> a string containing skill name
                       path -> a list containing the actions to be performed to reach a certain possible target
                       arg1 -> extra optional output (target's coordinates in this case)
        """

        if stats[21] < 1:
            return None, None, None
        path, coords = self.standard_plan([(37, -1)], False, safe_play)
        if path is None or len(path) == 0:
            return None, None, None
        else:
            return self.name, path, coords

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        rew, done, info = self.do_plan(path)
        if rew == -1:
            self.game.clear_memory(arg1[0], arg1[1])
            return None, None, None
        # agent = self.game.get_agent_position()
        stats = self.game.get_bl_stats()
        parsed_all = self.game.parse_all()
        gnam = False
        if parsed_all.__contains__("kobold") or \
                parsed_all.__contains__("rabid") or \
                parsed_all.__contains__("bat") or \
                parsed_all.__contains__("guardian naga") or \
                parsed_all.__contains__("yellow mold") or \
                parsed_all.__contains__("were") or \
                parsed_all.__contains__("soldier ant") or \
                parsed_all.__contains__("homunculus"):
            self.game.append_inedible((arg1[0], arg1[1]))
            return None, None, None
        elif parsed_all.__contains__("lichen") or \
                parsed_all.__contains__("ration") or \
                parsed_all.__contains__("melon") or \
                parsed_all.__contains__("apple") or \
                parsed_all.__contains__("gunyoki") or \
                parsed_all.__contains__("pear") or \
                parsed_all.__contains__("leaf") or \
                parsed_all.__contains__("carrot") or \
                parsed_all.__contains__("garlic") or \
                parsed_all.__contains__("meat") or \
                parsed_all.__contains__("egg") or \
                (parsed_all.__contains__("orange") and
                 not parsed_all.__contains__("gem") and
                 not parsed_all.__contains__("potion")) or \
                parsed_all.__contains__("banana") or \
                parsed_all.__contains__("wafer") or \
                parsed_all.__contains__("candy") or \
                parsed_all.__contains__("cookie") or \
                parsed_all.__contains__("jelly") or \
                parsed_all.__contains__("pie") or \
                parsed_all.__contains__("pancake") or \
                parsed_all.__contains__("wolfsbane") or \
                parsed_all.__contains__("tin") or \
                parsed_all.__contains__("kelp frond") or \
                parsed_all.__contains__("lizard"):
            self.game.do_it(35, None)  # eat
            message = self.game.get_parsed_message()
            if message.__contains__("corpse") and \
                    not (message.__contains__("lichen") or message.__contains__("lizard")):
                if not self.fresh_food():
                    self.game.no()
                    self.game.append_inedible((arg1[0], arg1[1]))  # temporaneo
            elif message.__contains__("eat") and message.__contains__("?"):
                self.game.yes()
                gnam = True
        elif self.fresh_food():
            self.game.do_it(35, None)  # eat
            message = self.game.get_parsed_message()
            if message.__contains__("eat") and message.__contains__("?"):
                self.game.yes()
                gnam = True
        #elif stats[21] == 4:
            #self.game.reset_inedible()
            #self.game.do_it(35, None)  # eat
            #message = self.game.get_parsed_message()
            #if message.__contains__("eat") and message.__contains__("?"):
                #self.game.yes()
                #gnam = True
        if not gnam:
            self.game.append_inedible((arg1[0], arg1[1]))
        return None, None, None


class Break(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def planning(self, stats, safe_play, agent):
        """
               function for skill planning

               :param safe_play: flag identifying the need for a safe play
               :param agent: actual agent position according to agent's knowledge
               :param stats: actual in-game character's stats according to agent's knowledge
               :return name -> a string containing skill name
                       path -> a list containing the actions to be performed to reach a certain possible target (None)
                       arg1 -> extra optional output (None)
        """

        near = self.game.neighbors_8_dir(agent[0], agent[1])
        for tile in near:
            if self.game.is_a_monster(tile[0], tile[1]):
                return None, None, None
        if stats[21] <= 2 and self.game.get_risk(agent[0], agent[1]) == 0 and stats[11] != 0 \
                and (stats[10] / stats[11]) < 0.65:
            return self.name, None, None

    def execution(self, path, arg1, agent, stats):
        """
             function for skill execution

             :param path: path to be followed
             :param arg1: optional extra argument of skill's execution (position of the target to be reached)
             :param agent: actual agent position according to agent's knowledge
             :param stats: actual in-game character's stats according to agent's knowledge
             :return path to and position of a found tile
         """

        rew, done, info = self.game.do_it(38, None)  # esc, per evitare strane situe
        if not done:
            rew, done, info = self.game.do_it(75, None)  # search per aspettare con value
            agent = self.game.get_agent_position()
            message = self.game.get_parsed_message()
            if message.__contains__("hit") or \
                    message.__contains__("bite") or \
                    message.__contains__("attack") or \
                    message.__contains__("throw") or \
                    message.__contains__("swing"):
                self.game.force_risk(agent[0], agent[1], 2)
        return rew, done, info
