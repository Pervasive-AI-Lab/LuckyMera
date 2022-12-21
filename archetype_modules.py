# archetipo per ogni possibile tipo di task
class Task:
    def __init__(self, dungeon_walker, game, task_name):
        self.dungeon_walker = dungeon_walker
        self.game = game
        self.name = task_name

    # condizione per interrompere con emergenza ciò che si sta facendo
    def eject_button(self):
        if self.game.update_agent():
            self.game.update_obs()
            agent = self.game.get_agent_position()

            if self.game.get_risk(agent[0], agent[1]) > 1:
                self.game.notify_recently_ejected()
                return True
        return False

    @staticmethod
    def custom_contain(item_list, value):
        for item in item_list:
            if item[0] == value:
                return True, (item[1], item[2])
        return False, (-1, -1)

    def surely_not_a_trap(self, y, x):
        for log in self.game.get_recently_killed():
            if log[2] == y and log[3] == x:
                return True
        return False

    # metodo per l'esecuzione di piani articolati
    def do_plan(self, plan):
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
                                                                                                       next_tile[
                                                                                                           1]):  # se la prossima casella contiene del cibo
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
            if message.__contains__("It's solid stone.") or \
                    message.__contains__("It's a wall.") or \
                    message.__contains__("You can't move diagonally into an intact doorway.") or \
                    message.__contains__("You try to move the boulder, but in vain.") or \
                    message.__contains__("Perhaps that's why you cannot move it.") or \
                    message.__contains__("You hear a monster behind the boulder."):
                self.game.append_exception(next_tile)
                return -1, False, None  # failure
            if self.eject_button():
                return -1, False, None
            i += 1
        return rew, done, info

    def standard_condition(self, tile, args):
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

    # metodo ausiliario per la ricerca e il pathfinding verso un gruppo di obbiettivi generici
    def standard_plan(self, glyphs, not_reach_diag, safe_play):
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


# archetipo per task che prevedono il raggiungimento di un obbiettivo
class ReachTask(Task):
    def __init__(self, dungeon_walker, game, task_name):
        super().__init__(dungeon_walker, game, task_name)

    def execution(self, path, arg1, agent, stats):
        rew, done, info = self.do_plan(path)
        if rew == -1:
            self.game.clear_memory(arg1[0], arg1[1])
        return rew, done, info


# archetipo per task che prevedono la ricerca di percorsi nascosti
class HiddenTask(Task):
    def __init__(self, dungeon_walker, game, task_name):
        super().__init__(dungeon_walker, game, task_name)

    def condition_unsearched_obj(self, tile, args):
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

    # metodo ausiliario per la ricerca e il pathfinding verso un obbiettivo in cui non è mai stata effettuata una search
    def unsearched_plan(self, glyph, safe_play):
        found, y, x = self.game.find(self.condition_unsearched_obj, glyph)
        if found:
            return self.basic_pathfinder(safe_play, y, x)
        return None, (-1, -1)

    def execution(self, path, arg1, agent, stats):  # in search room corridor
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
