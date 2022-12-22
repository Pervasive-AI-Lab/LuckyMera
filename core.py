import math
import gym
from gym.spaces import Dict
import minihack
from nle import nethack
from typing import Dict
from queue import PriorityQueue
import time
import sys
import numpy

numpy.set_printoptions(threshold=sys.maxsize)

env = gym.make('NetHackChallenge-v0', )


class GameWhisperer:

    def __init__(self, fast_mode):
        self.a_yx = [-1, -1]
        self.walkable_glyphs = [(33, -1), (34, -1), (35, 7), (35, 15), (36, -1), (37, -1), (40, -1), (41, -1), (42, -1),
                                (46, -1),
                                (47, -1), (45, 3), (60, -1), (61, -1), (62, -1), (63, -1), (64, 15), (91, -1), (92, -1),
                                (93, -1),
                                (96, -1), (100, 15), (100, 7), (102, 15), (102, 7), (117, -1), (124, 3)]
        self.size_y = 21
        self.size_x = 79
        self.current_obs = env.reset()
        self.glyph_obs = self.current_obs.__getitem__("glyphs")
        self.char_obs = self.current_obs.__getitem__("chars")
        self.color_obs = self.current_obs.__getitem__("colors")
        self.message = self.current_obs.__getitem__("message")
        self.parsed_message = self.parse_message()
        self.all_obs = self.current_obs.__getitem__("tty_chars")
        self.bl_stats = self.current_obs.__getitem__("blstats")
        self.memory = [[-1 for _ in range(self.size_x)] for _ in range(self.size_y)]
        self.exception = []
        self.search_map = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]
        self.risk_map = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]
        self.last_risk_update = 0
        self.act_num = 0
        self.score = 0
        self.total_score = 0
        self.cooldown = 100000
        self.default_search_max = 10
        self.default_hard_search_max = 10
        self.search_max = self.default_search_max
        self.hard_search_max = self.default_hard_search_max
        self.agent_id = -1
        self.update_agent()
        self.agent_id = self.glyph_obs[self.a_yx[0]][self.a_yx[1]]
        self.memory[self.a_yx[0]][self.a_yx[0]] = self.act_num
        self.safe_play = False
        self.strict_safe_play = False  # quando la strategia prevede la sicurezza più categorica
        self.recently_ejected = False
        self.last_monster_searched = (-1, -1, 0)
        self.monster_exception = []
        self.engraved_tiles = []
        self.inedible = []
        self.recently_killed = []
        self.shop_tiles = []
        self.last_pray = -1
        self.old_turn = 0
        self.new_turn = 0
        self.panic = False
        self.pet_alive = False
        self.pet_alive_turn = 0
        self.ran = False
        self.ran_turn = 0
        self.ran_cooldown = 2
        self.guard_encounter = 0
        self.u_stairs_locations = []
        self.d_stairs_locations = []
        self.fast_mode = fast_mode
        self.stuck_counter = 0
        self.hard_search_num = 0
        # if not self.fast_mode:
        # env.render()

    def calculate_risk(self, y, x):
        touched = []
        layer = self.neighbors_8_dir(y, x)
        self.risk_map[y][x] += 2
        for tile in layer:
            self.risk_map[tile[0]][tile[1]] += 2
            touched.append((tile[0], tile[1]))

        for tile in layer:
            second_layer = self.neighbors_8_dir(tile[0], tile[1])
            for s_tile in second_layer:
                if not touched.__contains__((s_tile[0], s_tile[1])):
                    self.risk_map[s_tile[0]][s_tile[1]] += 1
                    touched.append((s_tile[0], s_tile[1]))

    # metodo per l'aggiornamento dell'osservazione dei pericoli
    def update_riskmap(self):
        self.risk_map = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]

        for y in range(self.size_y):
            for x in range(self.size_x):
                if self.is_a_monster(y, x):
                    self.calculate_risk(y, x)

    # metodo per l'aggiornamento dell'osservazione
    def update_obs(self):
        self.glyph_obs = self.current_obs.__getitem__("glyphs")
        self.char_obs = self.current_obs.__getitem__("chars")
        self.color_obs = self.current_obs.__getitem__("colors")
        self.message = self.current_obs.__getitem__("message")
        self.parsed_message = self.parse_message()
        self.bl_stats = self.current_obs.__getitem__("blstats")
        self.all_obs = self.current_obs.__getitem__("tty_chars")

        if self.last_risk_update != self.bl_stats[20]:
            self.update_riskmap()
            self.last_risk_update = self.bl_stats[20]

    def crop_printer(self, obs):
        print(obs[self.a_yx[0] - 2][self.a_yx[1] - 2], " ",
              obs[self.a_yx[0] - 2][self.a_yx[1] - 1], " ",
              obs[self.a_yx[0] - 2][self.a_yx[1]], " ",
              obs[self.a_yx[0] - 2][self.a_yx[1] + 1], " ",
              obs[self.a_yx[0] - 2][self.a_yx[1] + 2], " ")
        print(obs[self.a_yx[0] - 2][self.a_yx[1] - 2], " ",
              obs[self.a_yx[0] - 1][self.a_yx[1] - 1], " ",
              obs[self.a_yx[0] - 1][self.a_yx[1]], " ",
              obs[self.a_yx[0] - 1][self.a_yx[1] + 1], " ",
              obs[self.a_yx[0] - 1][self.a_yx[1] + 2], " ")
        print(obs[self.a_yx[0]][self.a_yx[1] - 2], " ",
              obs[self.a_yx[0]][self.a_yx[1] - 1], " ",
              obs[self.a_yx[0]][self.a_yx[1]], " ",
              obs[self.a_yx[0]][self.a_yx[1] + 1], " ",
              obs[self.a_yx[0]][self.a_yx[1] + 2], " ")
        print(obs[self.a_yx[0] + 1][self.a_yx[1] - 2], " ",
              obs[self.a_yx[0] + 1][self.a_yx[1] - 1], " ",
              obs[self.a_yx[0] + 1][self.a_yx[1]], " ",
              obs[self.a_yx[0] + 1][self.a_yx[1] + 1], " ",
              obs[self.a_yx[0] + 1][self.a_yx[1] + 2], " ")
        print(obs[self.a_yx[0] + 2][self.a_yx[1] - 2], " ",
              obs[self.a_yx[0] + 2][self.a_yx[1] - 1], " ",
              obs[self.a_yx[0] + 2][self.a_yx[1]], " ",
              obs[self.a_yx[0] + 2][self.a_yx[1] + 1], " ",
              obs[self.a_yx[0] + 2][self.a_yx[1] + 2], " ")

    def debug_crop(self):
        self.crop_printer(self.char_obs)
        self.crop_printer(self.color_obs)
        self.crop_printer(self.glyph_obs)
        print(self.exception)

    def glyph_cooldown(self, glyph):
        if self.recently_ejected:
            self.recently_ejected = False
            return -1
        char = glyph[0]
        color = glyph[1]
        cooldown = self.cooldown
        if char == 64 and color == 15:
            cooldown = -1
        elif char == 43 and color == 3:
            cooldown = 50
        elif char == 45 or char == 124 and color == 3:
            cooldown = 200
        elif char == 62 or char == 36 or char == 60:
            cooldown = 15
        elif char == 37:
            cooldown = 1
        elif [58, 59, 38, 44].__contains__(char) or 65 <= char <= 90 or 97 <= char <= 122:
            cooldown = 5
        return cooldown

    def find(self, condition, args):
        frontier = list()
        looked_mat = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]
        current = (self.a_yx[0], self.a_yx[1])
        found = False

        while current is not None and not found:
            looked_mat[current[0]][current[1]] = 1

            if condition(current, args):
                return True, current[0], current[1]

            nbh = self.neighbors_8_dir(current[0], current[1])

            for next_tile in nbh:
                if looked_mat[next_tile[0]][next_tile[1]] == 0 and not frontier.__contains__(next_tile):
                    frontier.append(next_tile)
            if len(frontier) > 0:
                current = frontier.pop(0)
            else:
                current = None

        return False, -1, -1

    def find_far(self, condition):
        frontier = list()
        looked_mat = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]
        current = (self.a_yx[0], self.a_yx[1])

        best = None

        while current is not None:
            looked_mat[current[0]][current[1]] = 1

            if condition(current[0], current[1]):
                best = current

            nbh = self.neighbors_8_dir(current[0], current[1])

            for next_tile in nbh:
                if looked_mat[next_tile[0]][next_tile[1]] == 0 and not frontier.__contains__(next_tile):
                    frontier.append(next_tile)
            if len(frontier) > 0:
                current = frontier.pop(0)
            else:
                current = None

        if best is not None:
            return True, best[0], best[1]
        else:
            return False, -1, -1

    def condition_agent_obj(self, tile, args):
        if args.__contains__((self.char_obs[tile[0]][tile[1]], self.color_obs[tile[0]][tile[1]])) and \
                (self.memory[tile[0]][tile[1]] == -1 or
                 abs(self.memory[tile[0]][tile[1]] - self.act_num) > self.glyph_cooldown(
                            (self.char_obs[tile[0]][tile[1]], self.color_obs[tile[0]][tile[1]]))) \
                and (self.agent_id == self.glyph_obs[tile[0]][tile[1]] or self.agent_id == -1):
            return True
        else:
            return False

    # metodo che individua e aggiorna la posizione dell'agente
    def update_agent(self):
        found_agent, self.a_yx[0], self.a_yx[1] = self.find(self.condition_agent_obj, [(64, 15)])
        return found_agent

    def hard_search(self):
        self.search_map = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]
        self.search_max = self.hard_search_max
        self.hard_search_max -= 1

    # metodo che effettua il reset della memoria dell'agente
    def reset_memory(self):
        self.exception = []
        self.monster_exception = []
        self.search_max = self.default_search_max
        self.hard_search_max = self.default_hard_search_max
        self.memory = [[-1 for _ in range(self.size_x)] for _ in range(self.size_y)]
        self.search_map = [[0 for _ in range(self.size_x)] for _ in range(self.size_y)]

    def unexplored_walkable_around(self, y, x):
        walkable = 0
        unex_walkable = 0
        door_flag = False
        for i in self.neighbors_8_dir(y, x):
            if self.is_doorway(i[0], i[1]):
                door_flag = True
            if self.char_obs[i[0]][i[1]] == 43 or self.char_obs[i[0]][i[1]] == 96:
                return True
            if self.is_a_monster(i[0], i[1]):
                return True
            if self.is_walkable(i[0], i[1]):
                walkable += 1
            if self.is_walkable(i[0], i[1]) and self.is_unexplored(i[0], i[1]):
                unex_walkable += 1

        if door_flag and walkable == 1 and unex_walkable == 0:
            return False
        if door_flag:
            return True
        if walkable >= 3 or unex_walkable >= 1:
            return True

        return False

    # metodo per stabilire se una casella vada o meno considerata inesplorata
    def is_unexplored(self, y, x):
        if self.memory[y][x] == -1 or abs(self.memory[y][x] - self.act_num) >= self.cooldown:
            return True
        else:
            return False

    def is_walkable(self, y, x):

        char = self.char_obs[y][x]
        color = self.color_obs[y][x]

        if char == 64 and (y != self.a_yx[0] or x != self.a_yx[1]):
            return False

        if self.shop_tiles.__contains__((y, x)):
            return False

        if char == 101 and not self.panic:  # spore or eye
            return False
        elif char == 70 and color != 10 and color != 5 and not self.panic and self.bl_stats[10] < 15:  # Molds
            return False
        # elif char == 98 and color == 2 and not self.panic:  # Acid Blob
        #    return False

        if char == 43 and color != 3:
            return True

        if (self.walkable_glyphs.__contains__((char, color)) or self.walkable_glyphs.__contains__(
                (char, -1))) and not self.exception.__contains__((y, x)):
            if char == 64 and (self.glyph_obs[y][x] != self.agent_id or color != 15):
                return False
            return True
        else:
            return False

    def is_a_monster(self, y, x):
        char = self.char_obs[y][x]
        color = self.color_obs[y][x]

        if self.monster_exception.__contains__((y, x)):
            return False
        # if char == 104 and self.bl_stats[12] >= 3:
        # return False
        if char == 64 and color != 15:
            return True
        if [58, 59, 38, 39, 44].__contains__(char) or 65 <= char <= 90 or 97 <= char <= 122:
            if (char == 102 or char == 100) and (
                    color == 7 or color == 15) and self.pet_alive:  # or (find and self.is_unexplored(y, x)):
                return False
            elif char == 117 and color == 3 and self.pet_alive:  # il pony amico non è un mostro
                return False
            elif char == 101 and not self.panic:  # spore or eye
                return False
            elif char == 70 and color != 10 and color != 5 and not self.panic and self.bl_stats[10] < 15:  # Molds
                return False
            # elif char == 98 and color == 2 and not self.panic:  # Acid Blob
            #    return False
            else:
                return True
        else:
            return False

    def is_safe(self, y, x):
        if self.risk_map[y][x] > 0:
            return False
        else:
            return True

    def is_unsearched_wallside(self, y, x):

        if y < self.size_y - 1:
            if (self.char_obs[y + 1][x] == 124 or self.char_obs[y + 1][x] == 45) and \
                    self.color_obs[y + 1][x] == 7 and self.search_map[y + 1][x] == 0:
                return True
        if y > 0:
            if (self.char_obs[y - 1][x] == 124 or self.char_obs[y - 1][x] == 45) and \
                    self.color_obs[y - 1][x] == 7 and self.search_map[y - 1][x] == 0:
                return True
        if x < self.size_x - 1:
            if (self.char_obs[y][x + 1] == 124 or self.char_obs[y][x + 1] == 45) and \
                    self.color_obs[y][x + 1] == 7 and self.search_map[y][x + 1] == 0:
                return True
        if x > 0:
            if (self.char_obs[y][x - 1] == 124 or self.char_obs[y][x - 1] == 45) and \
                    self.color_obs[y][x - 1] == 7 and self.search_map[y][x - 1] == 0:
                return True
        return False

    def is_unsearched_voidside(self, y, x):

        if y < self.size_y - 1:
            if self.char_obs[y + 1][x] == 32 and self.search_map[y + 1][x] == 0:
                return True
        if y > 0:
            if self.char_obs[y - 1][x] == 32 and self.search_map[y - 1][x] == 0:
                return True
        if x < self.size_x - 1:
            if self.char_obs[y][x + 1] == 32 and self.search_map[y][x + 1] == 0:
                return True
        if x > 0:
            if self.char_obs[y][x - 1] == 32 and self.search_map[y][x - 1] == 0:
                return True
        return False

    def is_doorway(self, y, x):
        char = self.char_obs[y][x]
        color = self.color_obs[y][x]
        if (
                char == 43 or char == 124 or char == 45) and color == 3:  # or (char == 46 and self.is_unexplored(y, x)): wip
            return True
        walls_count_h = 0
        walls_count_v = 0
        if y < self.size_y - 1:
            if (self.char_obs[y + 1][x] == 124 or self.char_obs[y + 1][x] == 45) and \
                    self.color_obs[y + 1][x] == 7:
                walls_count_v += 1
        if y > 0:
            if (self.char_obs[y - 1][x] == 124 or self.char_obs[y - 1][x] == 45) and \
                    self.color_obs[y - 1][x] == 7:
                walls_count_v += 1
        if x < self.size_x - 1:
            if (self.char_obs[y][x + 1] == 124 or self.char_obs[y][x + 1] == 45) and \
                    self.color_obs[y][x + 1] == 7:
                walls_count_h += 1
        if x > 0:
            if (self.char_obs[y][x - 1] == 124 or self.char_obs[y][x - 1] == 45) and \
                    self.color_obs[y][x - 1] == 7:
                walls_count_h += 1

        if walls_count_h == 2 or walls_count_v == 2:
            return True
        else:
            return False

    def is_isolated(self, y, x, glyph, cross):
        same_glyph_count = 0
        near = self.neighbors_8_dir(y, x)
        while len(near) > 0:
            next_tile = near.pop()
            if cross and next_tile[0] != y and next_tile[1] != x:
                continue
            if glyph is None:
                if self.glyph_obs[next_tile[0]][next_tile[1]] == self.glyph_obs[y][x] or self.is_doorway(next_tile[0],
                                                                                                         next_tile[1]):
                    same_glyph_count += 1
            else:
                char = glyph[0]
                color = glyph[1]
                if (self.char_obs[next_tile[0]][next_tile[1]] == char and self.color_obs[next_tile[0]][
                        next_tile[1]] == color) or self.is_doorway(next_tile[0], next_tile[1]):
                    same_glyph_count += 1
        if same_glyph_count < 2:
            return True
        else:
            return False

    def is_near_glyph(self, y, x, glyph, dir_num):
        char = glyph[0]
        color = glyph[1]
        around_it = []
        if dir_num == 8:
            around_it = self.neighbors_8_dir(y, x)
        if dir_num == 4:
            around_it = self.neighbors_4_dir(y, x)
        while len(around_it) > 0:
            near = around_it.pop()
            if self.char_obs[near[0]][near[1]] == char and (self.color_obs[near[0]][near[1]] == color or color == -1):
                return True
        return False

    def neighbors_8_dir(self, y, x):
        neighborhood = self.neighbors_4_dir(y, x)

        if y > 0:
            if x > 0:
                neighborhood.append((y - 1, x - 1))  # nw
            if x < self.size_x - 1:
                neighborhood.append((y - 1, x + 1))  # ne
        if x < self.size_x - 1:
            if y < self.size_y - 1:
                neighborhood.append((y + 1, x + 1))  # se
        if y < self.size_y - 1:
            if x > 0:
                neighborhood.append((y + 1, x - 1))  # sw

        return neighborhood

    def neighbors_4_dir(self, y, x):
        neighborhood = list()
        if y > 0:
            neighborhood.append((y - 1, x))  # n
        if x < self.size_x - 1:
            neighborhood.append((y, x + 1))  # e
        if y < self.size_y - 1:
            neighborhood.append((y + 1, x))  # s
        if x > 0:
            neighborhood.append((y, x - 1))  # w
        return neighborhood

    def neighbors(self, y, x, safe):
        neighborhood = list()
        doorway = self.is_doorway(y, x)
        if y > 0:
            if self.is_walkable(y - 1, x) and (not safe or self.is_safe(y - 1, x)):
                neighborhood.append((y - 1, x))  # n
            if x > 0:
                if self.is_walkable(y - 1, x - 1) and (not safe or self.is_safe(y - 1, x - 1)) and not doorway:
                    if not self.is_doorway(y - 1, x - 1):
                        neighborhood.append((y - 1, x - 1))  # nw
            if x < self.size_x - 1:
                if self.is_walkable(y - 1, x + 1) and (not safe or self.is_safe(y - 1, x + 1)) and not doorway:
                    if not self.is_doorway(y - 1, x + 1):
                        neighborhood.append((y - 1, x + 1))  # ne
        if x < self.size_x - 1:
            if self.is_walkable(y, x + 1) and (not safe or self.is_safe(y, x + 1)):
                neighborhood.append((y, x + 1))  # e
            if y < self.size_y - 1:
                if self.is_walkable(y + 1, x + 1) and (not safe or self.is_safe(y + 1, x + 1)) and not doorway:
                    if not self.is_doorway(y + 1, x + 1):
                        neighborhood.append((y + 1, x + 1))  # se
        if y < self.size_y - 1:
            if self.is_walkable(y + 1, x) and (not safe or self.is_safe(y + 1, x)):
                neighborhood.append((y + 1, x))  # s
            if x > 0:
                if self.is_walkable(y + 1, x - 1) and (not safe or self.is_safe(y + 1, x - 1)) and not doorway:
                    if not self.is_doorway(y + 1, x - 1):
                        neighborhood.append((y + 1, x - 1))  # sw
        if x > 0:
            if self.is_walkable(y, x - 1) and (not safe or self.is_safe(y, x - 1)):
                neighborhood.append((y, x - 1))  # w
        return neighborhood

    def parse_message(self):
        parsed_string = ""
        for c in self.message:
            parsed_string = parsed_string + chr(c)
        return parsed_string

    def parse_all(self):
        parsed_string = ""
        for i in range(0, 24):
            for j in range(0, 80):
                c = self.all_obs[i][j]
                parsed_string = parsed_string + chr(c)
        return parsed_string

    def yes(self):
        if self.update_agent():
            self.current_obs, rew, done, info = env.step(7)
        self.update_obs()

    def do_it(self, x, direction):
        # print(self.bl_stats)
        self.old_turn = self.bl_stats[20]
        rew = 0
        done = False
        info = None

        if not self.fast_mode:
            print("pray_timeout: ", abs(self.last_pray - self.bl_stats[20]))
        if self.bl_stats[20] % 100 == 0:
            print("guard_encounter: ", self.guard_encounter, " avanzamento - score: ", self.bl_stats[9], " turno: ",
                  self.bl_stats[20], " ora: ", time.localtime()[3], "-", time.localtime()[4], "pray_timeout: ",
                  abs(self.last_pray - self.bl_stats[20]), " -----")
            go_back(2)

        if abs(self.bl_stats[20] - self.pet_alive_turn) > 10 and self.bl_stats[20] > 3000:
            self.pet_alive = False

        if self.act_num % 50 == 0:  # modifica
            self.panic = False

        if self.ran:
            if abs(self.ran_turn - self.bl_stats[20]) > self.ran_cooldown:
                self.ran = False

        if self.parsed_message.__contains__("Closed for inventory"):
            for tile in self.neighbors_4_dir(self.a_yx[0], self.a_yx[1]):
                if self.char_obs[tile[0]][tile[1]] == 43 and self.color_obs[tile[0]][tile[1]] == 3:
                    self.shop_tiles.append(tile)

        if self.update_agent():
            self.current_obs, rew, done, info = env.step(38)

            if self.parsed_message.__contains__("Closed for inventory"):
                for tile in self.neighbors_4_dir(self.a_yx[0], self.a_yx[1]):
                    if self.char_obs[tile[0]][tile[1]] == 43 and self.color_obs[tile[0]][tile[1]] == 3:
                        self.shop_tiles.append(tile)

        if self.score < self.bl_stats[9]:
            self.score = self.bl_stats[9]

        if self.parsed_message.__contains__("Hello stranger, who are you?"):  # respond Croesus
            self.guard_encounter += 1
            return -1, True, None

        if self.update_agent():
            self.current_obs, rew, done, info = env.step(38)

        if self.update_agent():
            self.current_obs, rew, done, info = env.step(x)
        self.update_obs()

        if self.parsed_message.__contains__("swap"):
            self.pet_alive = True
            self.pet_alive_turn = self.bl_stats[20]
        if direction is not None and self.parsed_message.__contains__("In what direction?"):
            self.current_obs, rew, done, info = env.step(direction)
            self.update_obs()

        if self.parsed_message.__contains__("Are you sure you want to pray?") or self.parsed_message.__contains__(
                "Really attack"):
            self.yes()
        if self.parsed_message.__contains__("You are carrying too much to get through."):
            next_tile = self.inverse_move_translator(self.a_yx[0], self.a_yx[1], x)
            self.exception.append(next_tile)
            self.update_obs()
        if self.parsed_message.__contains__("What do you want to write with?"):
            self.current_obs, rew, done, info = env.step(106)  # -
            self.update_obs()
        if self.parsed_message.__contains__("You write in the dust with your fingertip."):
            self.current_obs, rew, done, info = env.step(19)  # more
            self.update_obs()
        if self.parsed_message.__contains__("What do you want to write in the dust here?"):
            self.current_obs, rew, done, info = env.step(36)  # E
            self.current_obs, rew, done, info = env.step(1)  # l
            self.current_obs, rew, done, info = env.step(6)  # b
            self.current_obs, rew, done, info = env.step(35)  # e
            self.current_obs, rew, done, info = env.step(67)  # r
            self.current_obs, rew, done, info = env.step(35)  # e
            self.current_obs, rew, done, info = env.step(91)  # t
            self.current_obs, rew, done, info = env.step(3)  # h
            self.current_obs, rew, done, info = env.step(19)  # more
            self.update_obs()

        if self.parsed_message.__contains__("You swap places"):
            self.pet_alive = True

        if self.parsed_message.__contains__("Closed for inventory"):
            for tile in self.neighbors_4_dir(self.a_yx[0], self.a_yx[1]):
                if self.char_obs[tile[0]][tile[1]] == 43 and self.color_obs[tile[0]][tile[1]] == 3:
                    self.shop_tiles.append(tile)

        if ((self.parsed_message.__contains__("Welcome") and self.parsed_message.__contains__(
                "\"")) or self.parsed_message.__contains__("\"How dare you break my door?\"")) \
                and not 0 <= self.bl_stats[20] <= 5:
            self.shop_propagation(self.a_yx)

        if self.bl_stats[11] != 0 and (self.bl_stats[10] / self.bl_stats[11]) <= 0.5 and not self.safe_play:
            if not self.fast_mode:
                print("SAFE_MODE : enabled")
            self.safe_play = True
        elif self.bl_stats[11] != 0 and (self.bl_stats[10] / self.bl_stats[11]) > 0.85 and self.safe_play:
            if not self.fast_mode:
                print("SAFE_MODE : disabled")
            self.safe_play = False
        self.act_num += 1
        if self.update_agent():
            self.memory[self.a_yx[0]][self.a_yx[1]] = self.act_num
            if x == 75:  # it was a search
                self.search_map[self.a_yx[0]][self.a_yx[1]] = 1
                for next_tile in self.neighbors_8_dir(self.a_yx[0], self.a_yx[1]):
                    self.search_map[next_tile[0]][next_tile[1]] = 1
        if not self.fast_mode:  # and x != 10:
            # go_back(27)
            env.render()
            time.sleep(0)
        self.new_turn = self.bl_stats[20]
        return rew, done, info

    def shop_propagation(self, tile):
        for near in self.neighbors_8_dir(tile[0], tile[1]):
            char = self.char_obs[near[0]][near[1]]
            if char == 124 or char == 45 or char == 35 or char == 32 or (
                    near[0] == self.a_yx[0] and near[1] == self.a_yx[
                    1]):  # or ([58,59,38,39,44].__contains__(char) or 65 <= char <= 90 or 97 <= char <= 122) :
                continue
            elif not self.shop_tiles.__contains__(near):
                self.shop_tiles.append(near)
                self.shop_propagation(near)

    @staticmethod
    def move_translator(from_y, from_x, to_y, to_x):
        if to_y > from_y:  # la y del next è maggiore -> movimenti verso sud
            if to_x > from_x:
                move = 5  # se
            elif to_x == from_x:
                move = 2  # s
            else:
                move = 6  # sw

        elif to_y == from_y:  # la y del next è uguale -> movimenti verso est ed ovest
            if to_x > from_x:
                move = 1  # e
            else:
                move = 3  # w
        else:  # la y del next è minore -> movimenti verso nord
            if to_x > from_x:
                move = 4  # ne
            elif to_x == from_x:
                move = 0  # n
            else:
                move = 7  # nw

        return move

    @staticmethod
    def inverse_move_translator(from_y, from_x, direction):
        if direction == 0:
            return from_y - 1, from_x
        elif direction == 4:
            return from_y - 1, from_x + 1
        elif direction == 1:
            return from_y, from_x + 1
        elif direction == 5:
            return from_y + 1, from_x + 1
        elif direction == 2:
            return from_y + 1, from_x
        elif direction == 6:
            return from_y + 1, from_x - 1
        elif direction == 3:
            return from_y, from_x - 1
        elif direction == 7:
            return from_y - 1, from_x - 1

    def reset_game(self):
        self.current_obs = env.reset()
        self.new_turn = 0
        self.old_turn = 0
        self.update_obs()
        self.reset_memory()
        self.safe_play = False
        self.agent_id = -1
        self.update_agent()
        self.agent_id = self.glyph_obs[self.a_yx[0]][self.a_yx[1]]
        self.memory[self.a_yx[0]][self.a_yx[1]] = self.act_num
        if not self.fast_mode:
            env.render()
        self.engraved_tiles = []
        self.inedible = []
        self.shop_tiles = []
        self.u_stairs_locations = []
        self.d_stairs_locations = []
        self.total_score += self.score
        self.score = 0
        self.recently_killed = []
        self.last_pray = -1

    def partial_reset_game(self):
        self.pet_alive = False
        self.update_obs()
        self.reset_memory()
        self.engraved_tiles = []
        self.recently_killed = []
        self.shop_tiles = []
        self.inedible = []

    def check_exception(self, tile):
        return self.exception.__contains__((tile[0], tile[1]))

    def append_exception(self, tile):
        self.exception.append(tile)

    def check_engraved(self, tile):
        return self.engraved_tiles.__contains__((tile[0], tile[1]))

    def append_engraved(self, tile):
        self.engraved_tiles.append(tile)

    def check_monster_exception(self, tile):
        return self.monster_exception.__contains__((tile[0], tile[1]))

    def append_monster_exception(self, tile):
        self.monster_exception.append(tile)

    def check_inedible(self, tile):
        return self.inedible.__contains__((tile[0], tile[1]))

    def append_inedible(self, tile):
        self.inedible.append(tile)

    def reset_inedible(self):
        self.inedible = []

    def get_recently_killed(self):
        return self.recently_killed

    def append_recently_killed(self, data):
        self.exception.append(data)

    def check_recently_ejected(self):
        return self.recently_ejected

    def notify_recently_ejected(self):
        self.recently_ejected = True

    def update_memory(self, y, x):
        self.memory[y][x] = self.act_num

    def clear_memory(self, y, x):
        self.memory[y][x] = -1

    def update_last_monster_searched(self, char, color, times):
        self.last_monster_searched = (char, color, times)

    def get_last_monster_searched(self):
        return self.last_monster_searched

    def get_agent_position(self):
        return self.a_yx

    def get_size_x(self):
        return self.size_x

    def get_size_y(self):
        return self.size_y

    def get_act_num(self):
        return self.act_num

    def get_memory(self, y, x):
        return self.memory[y][x]

    def get_risk(self, y, x):
        return self.risk_map[y][x]

    def force_risk(self, y, x, risk):
        self.risk_map[y][x] = risk

    def get_glyph(self, y, x):
        return self.glyph_obs[y][x]

    def get_char(self, y, x):
        return self.char_obs[y][x]

    def get_color(self, y, x):
        return self.color_obs[y][x]

    def get_parsed_message(self):
        return self.parsed_message

    def get_bl_stats(self):
        return self.bl_stats

    def get_safe_play(self):
        return self.safe_play

    def get_pet_alive(self):
        return self.pet_alive

    def get_actual_score(self):
        return self.score

    def get_total_score(self):
        return self.total_score

    def get_stairs_locations(self):
        return self.u_stairs_locations, self.d_stairs_locations

    def append_stairs_location(self, stairs, u):
        if u:
            self.u_stairs_locations.append(stairs)
        else:
            self.d_stairs_locations.append(stairs)

    def get_last_pray(self):
        return self.last_pray

    def update_last_pray(self):
        self.last_pray = self.bl_stats[20]

    def update_ran(self):
        self.ran = True
        self.ran_turn = self.bl_stats[20]

    def reset_ran(self):
        self.ran = False

    def get_ran(self):
        return self.ran

    def get_new_turn(self):
        return self.new_turn

    def get_old_turn(self):
        return self.old_turn

    def get_search_max(self):
        return self.search_max

    def stuck(self):
        self.stuck_counter += 1

    def reset_stuck_counter(self):
        self.stuck_counter = 0

    def get_stuck_counter(self):
        return self.stuck_counter

    def increment_hard_search_num(self):
        self.hard_search_num += 1

    def reset_hard_search_num(self):
        self.hard_search_num = 0

    def get_hard_search_num(self):
        return self.hard_search_num

    def get_fast_mode(self):
        return self.fast_mode


class DungeonWalker:

    def __init__(self, game):
        self.game = game

    # euristica per il calcolo della distanza tra due caselle della griglia 8-direzionale
    @staticmethod
    def h_octile_distance(ay, ax, oy, ox):
        x_d = abs(ax - ox)
        y_d = abs(ay - oy)
        return (1.414 * min(x_d, y_d)) + abs(x_d - y_d)

    def a_star(self, oy, ox, safe):
        # voglio che restituisca il cammino
        # lista di priorità rappresentante la frontiera
        frontier = PriorityQueue()
        agent = self.game.get_agent_position()
        # inizializzo l'algoritmo inserendo nella lista il nodo iniziale (posizione agente) (priorità massima ->0)
        frontier.put(((agent[0], agent[1]), 0))
        # dizionario in cui associo ai nodi il predecessore
        came_from: Dict[Location, Optional[Location]] = {}
        # dizionario in cui associo ai nodi il costo f(n) accumalatovi
        cost_so_far: Dict[Location, float] = {}
        came_from[(agent[0], agent[1])] = None
        cost_so_far[(agent[0], agent[1])] = 0

        while not frontier.empty():
            current = frontier.get()

            if current == (oy, ox):  # abbiamo raggiunto il goal
                break
            near = self.game.neighbors(current[0][0], current[0][1], safe)
            for next_tile in near:  # per cella adiacente alla corrente
                new_cost = cost_so_far[current[0]] + 1
                if next_tile not in cost_so_far or new_cost < cost_so_far[next_tile]:
                    cost_so_far[next_tile] = new_cost
                    priority = new_cost + self.h_octile_distance(next_tile[0], next_tile[1], oy, ox)
                    frontier.put((next_tile, priority))
                    came_from[next_tile] = current[0]
        return came_from, cost_so_far

    def path_finder(self, oy, ox, not_reach_diag, safe_play):

        yellow_brick_road = list()

        agent = self.game.get_agent_position()
        if self.game.get_risk(agent[0], agent[1]) >= 2 and safe_play:
            return yellow_brick_road

        came_from, cost_so_far = self.a_star(oy, ox, safe_play)
        cursor = (oy, ox)
        next_tile = None
        while cursor is not None:
            if next_tile is not None:

                if not_reach_diag and next_tile[0] == oy and next_tile[1] == ox and next_tile[0] != cursor[0] and \
                        next_tile[1] != cursor[1]:
                    # il prossimo nodo è l'obbiettivo e non deve essere raggiunto in diagonale
                    if next_tile[0] > cursor[0] and next_tile[1] > cursor[1]:  # y e x maggiori -> se
                        if self.game.is_walkable(cursor[0], cursor[1] + 1):
                            yellow_brick_road.append(2)  # s
                            yellow_brick_road.append(1)  # e
                        elif self.game.is_walkable(cursor[0] + 1, cursor[1]):
                            yellow_brick_road.append(1)  # e
                            yellow_brick_road.append(2)  # s
                    elif next_tile[0] > cursor[0] and next_tile[1] < cursor[1]:  # y maggiore e x minore -> sw
                        if self.game.is_walkable(cursor[0], cursor[1] - 1):
                            yellow_brick_road.append(2)  # s
                            yellow_brick_road.append(3)  # w
                        elif self.game.is_walkable(cursor[0] + 1, cursor[1]):
                            yellow_brick_road.append(3)  # w
                            yellow_brick_road.append(2)  # s
                    elif next_tile[0] < cursor[0] and next_tile[1] < cursor[1]:  # y minore e x maggiore -> nw
                        if self.game.is_walkable(cursor[0], cursor[1] - 1):
                            yellow_brick_road.append(0)  # n
                            yellow_brick_road.append(3)  # w
                        elif self.game.is_walkable(cursor[0] - 1, cursor[1]):
                            yellow_brick_road.append(3)  # w
                            yellow_brick_road.append(0)  # n
                    elif next_tile[0] < cursor[0] and next_tile[1] > cursor[1]:  # y minore e x minore -> ne
                        if self.game.is_walkable(cursor[0], cursor[1] + 1):
                            yellow_brick_road.append(0)  # n
                            yellow_brick_road.append(1)  # e
                        elif self.game.is_walkable(cursor[0] - 1, cursor[1]):
                            yellow_brick_road.append(1)  # e
                            yellow_brick_road.append(0)  # n

                yellow_brick_road.append(self.game.move_translator(cursor[0], cursor[1], next_tile[0], next_tile[1]))
            next_tile = cursor
            try:
                cursor = came_from[cursor]
            except:
                return None

        return yellow_brick_road


# metodo che pianifica la task da eseguire in un dato stato
def planning(game, tasks_prio, task_map):
    if game.get_new_turn() == game.get_old_turn():
        game.stuck()
    else:
        game.reset_stuck_counter()

    if not game.update_agent():
        return "failure", None, None
    else:
        game.update_obs()

    stats = game.get_bl_stats()
    safe_play = game.get_safe_play()
    agent = game.get_agent_position()

    while len(tasks_prio) > 0:
        task_name = tasks_prio.pop(0)
        task = task_map[task_name]

        out = task.planning(stats, safe_play, agent)
        if out is not None:
            task_name_o = out[0]
            path = out[1]
            arg1 = out[2]
            if task_name_o is not None:
                return task_name, path, arg1

    return "failure", None, None


# metodo che esegue le task pianificata
def main_logic(dungeon_walker, game, tasks_prio, task_map, attempts):
    success = 0
    scores = []
    mediana = 0

    for i in range(0, attempts):

        if game.get_fast_mode():
            if game.get_act_num != 0 and i != 0:
                scores.append(game.get_actual_score())
                size = len(scores)
                center = math.floor(size / 2)
                scores.sort()
                if (size % 2) == 1:
                    mediana = scores[center]
                else:
                    mediana = (scores[center] + scores[center - 1]) / 2

        done = False
        game.reset_hard_search_num()
        rew = 0
        game.reset_game()
        game.reset_stuck_counter()

        if game.get_fast_mode():
            go_back(3)
            true_divisor = i
            if true_divisor == 0:
                true_divisor = 1
            face = "(ಠ_ಠ)"
            if mediana < 475 and i != 0:
                face = "(╥︣﹏᷅╥)"
            if mediana >= 681:
                face = "(ง'-')ง"
            if mediana >= 756:
                face = "ᕙ(`▿´)ᕗ"
            print("// mean score: ", game.get_total_score() / true_divisor, "// median: ", mediana, " // games: ",
                  len(scores), "      ", face, "               ")
            print(scores)

        while not done:
            task, path, arg1 = planning(game, tasks_prio.copy(), task_map)
            if not game.get_fast_mode():
                print("TASK: ", task, " PATH: ", path)

            if not game.update_agent() or game.get_stuck_counter() > 200:
                break

            agent = game.get_agent_position()
            stats = game.get_bl_stats()

            if task == "failure":
                hs_n = game.get_hard_search_num()
                if not game.update_agent() or hs_n > 200:
                    break
                elif hs_n > 20:
                    dungeon_walker.panic = True
                if hs_n % 2 == 0 and hs_n != 0:
                    game.reset_memory()
                game.hard_search()
                game.increment_hard_search_num()
                rew, done, info = game.do_it(75, None)  # search per aspettare con value
            else:
                rew, done, info = task_map[task].execution(path, arg1, agent, stats)

        if rew == 1:
            success += 1


def go_back(num_lines):  # funzione per sovrascrivere lo schermo attuale
    print("\033[%dA" % num_lines)
