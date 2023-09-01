# abstract class for every possible type of skill
class Skill:
    def __init__(self, dungeon_walker, game, skill_name):
        self.dungeon_walker = dungeon_walker
        self.game = game
        self.name = skill_name

    # condition to interrupt currect actions in case of emergency
    def eject_button(self):
        """
            function that controls whether the agent should quickly flee from the current plan

            :return: TRUE -> if agent is not safe, FALSE -> elsewise
        """

        if self.game.update_agent():
            self.game.update_obs()
            agent = self.game.get_agent_position()

            if self.game.get_risk(agent[0], agent[1]) > 1 or self.game.get_bl_stats()[21] == 4:
                self.game.notify_recently_ejected()
                return True
        return False

    @staticmethod
    def custom_contain(item_list, value):
        """
            function that checks if a given list contains a particular value

            :param item_list: the list to be explored
            :param value: the value searched in list's items
            :return: TRUE -> if the list contain the given value, FALSE -> elsewise
                     if TRUE, function returns the remaining part of the item found
        """

        for item in item_list:
            if item[0] == value:
                return True, (item[1], item[2])
        return False, (-1, -1)

    def surely_not_a_trap(self, y, x):
        """
            function that checks for traps on a sus tile

            :param y: y value of the given tile
            :param x: x value of the given tile
            :return: TRUE -> if the sus tile is safe, FALSE -> elsewise
        """

        if self.game.get_bl_stats()[12] != 1:
            return True

        for log in self.game.get_recently_killed():
            if log[2] == y and log[3] == x:
                return True
        return False

    # method to execute articulate plans
    def do_plan(self, plan):
        """
            function that perform multiple actions according to a given plan

            :param plan: planned action list
            :return: :return: the "reward" value (1 if episode success, 0 elsewise),
                     the "done" value (TRUE if the episode endend, FALSE elsewise),
                     the "info" object containg extra information (Gym standard implementation)
        """

        size = len(plan)
        done = False
        info = None
        rew = 0
        i = 0
        while 0 <= i < size and not done:
            action = plan.pop()
            agent = self.game.get_agent_position()
            next_tile = self.game.inverse_move_translator(agent[0], agent[1], action)
            if self.game.update_agent():
                if self.game.get_char(next_tile[0], next_tile[1]) == 37 and not self.surely_not_a_trap(next_tile[0],
                                                                                                       next_tile[1]):  # se la prossima casella contiene del cibo
                    for k in range(0, 10):
                        # modifica 1.1
                        self.game.do_it(96, action)  # untrap
                if self.game.is_walkable(next_tile[0], next_tile[1]):
                    rew, done, info = self.game.do_it(action, None)
                else:
                    return -1, False, None  # failure
            else:
                rew = 0
                done = True
                break
            message = self.game.get_parsed_message()
            if any(message.__contains__(m) for m in ["It's solid stone.",
                                                     "It's a wall.",
                                                     "You can't move diagonally into an intact doorway.",
                                                     "You try to move the boulder, but in vain.",
                                                     "Perhaps that's why you cannot move it.",
                                                     "You hear a monster behind the boulder."]):
                self.game.append_exception(next_tile)
                return -1, False, None  # failure
            if self.eject_button():
                return -1, False, None
            i += 1
        return rew, done, info

    def standard_condition(self, tile, args):
        """
            condition function for identifying a tile according to a list of possible tiles

            :param tile: tile to verify
            :param args: arguments for the given condition (list of correct tiles combinations)
            :return TRUE -> if condition is verified, FALSE -> elsewise
        """

        if (args.__contains__((self.game.get_char(tile[0], tile[1]), self.game.get_color(tile[0], tile[1]))) or
            ((self.game.get_char(tile[0], tile[1]) == 36 or
              (self.game.get_char(tile[0], tile[1]) == 37 and not self.game.check_inedible(
                  tile))) and args.__contains__((self.game.get_char(tile[0], tile[1]), -1)))) and \
                not (self.game.check_exception(tile) and self.game.get_char(tile[0], tile[1]) == 43) and \
                (self.game.get_memory(tile[0], tile[1]) == -1 or
                 abs(self.game.get_memory(tile[0], tile[1]) - self.game.get_act_num()) > self.game.glyph_cooldown(
                            (self.game.get_char(tile[0], tile[1]), self.game.get_color(tile[0], tile[1])))):
            return True
        else:
            return False

    # auxiliary method for the seach and pathfinding towards a group of generic goal positions
    def standard_plan(self, glyphs, not_reach_diag, safe_play):
        """
            function for finding a path to a tile given a set of possible objective

            :param glyphs: set of possible objective tiles
            :param not_reach_diag: flag identifying a tile which cant be reachen diagonally
            :param safe_play: flag identifying the need for a safe play
            :return path to and position of a found tile
        """

        found, y, x = self.game.find(self.standard_condition, glyphs)
        if found:
            char = self.game.get_char(y, x)
            stats = self.game.get_bl_stats()
            if char == 60 and not self.custom_contain(self.game.get_stairs_locations()[0], stats[12])[0]:
                self.game.append_stairs_location((stats[12], y, x), True)

            if char == 62 and not self.custom_contain(self.game.get_stairs_locations()[1], stats[12])[0]:
                self.game.append_stairs_location((stats[12], y, x), False)

            path = self.dungeon_walker.path_finder(y, x, not_reach_diag, safe_play)
            self.game.update_memory(y, x)
            return path, (y, x)
        return None, (-1, -1)

    def basic_pathfinder(self, safe_play, y, x):
        path = self.dungeon_walker.path_finder(y, x, False, safe_play)
        self.game.update_memory(y, x)
        return path, (y, x)

    def planning(self, stats, safe_play, agent):
        return self.name, None, None

    def execution(self, path, arg1, agent, stats):
        return 0, False, None

    def get_name(self):
        return self.name


# class for skills to reach a goal position
class ReachSkill(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def execution(self, path, arg1, agent, stats):
        """
            function for skill's execution

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


# class for skills to search for hidden parts
class HiddenSkill(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    def condition_unsearched_obj(self, tile, args):
        """
            condition function for identifying a tile according to a list of possible tiles
            looking for a tile where agent haven't performed enough searches yet

            :param tile: tile to verify
            :param args: arguments for the given condition (list of correct tiles combinations)
            :return TRUE -> if condition is verified, FALSE -> elsewise
        """

        glyph = args[0]
        char = glyph[0]
        color = glyph[1]
        if self.game.get_char(tile[0], tile[1]) == char and self.game.get_color(tile[0], tile[1]) == color:
            if char == 46:
                if self.game.is_unsearched_wallside(tile[0], tile[1]):
                    return True
            elif char == 35 and color == 7:
                if self.game.is_unsearched_voidside(tile[0], tile[1]):
                    return True
        return False

    # auxiliary methods for search and pathfinding towards a goal position never searched before
    def unsearched_plan(self, glyph, safe_play):
        """
            function for finding a path to a tile containing the given glyph according to the unsearched condition (previous  function)

            :param glyph: objective tile appearence on screen
            :param safe_play: flag identifying the need for a safe play
            :return path to and position of a found tile
        """

        found, y, x = self.game.find(self.condition_unsearched_obj, glyph)
        if found:
            return self.basic_pathfinder(safe_play, y, x)
        return None, (-1, -1)

    def execution(self, path, arg1, agent, stats):  # in search room corridor
        """
            function for skill's execution

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
        if not done and rew != -1:
            j = 0
            while j < self.game.get_search_max() and not done and not self.game.get_parsed_message().__contains__(
                    "You find") and not self.eject_button():
                if not self.game.get_fast_mode():
                    print(self.name, " try: ", j)

                if 3 <= stats[21] <= 4:
                    break

                rew, done, info = self.game.do_it(75, None)  # search
                stats = self.game.get_bl_stats()
                j += 1
        return rew, done, info
