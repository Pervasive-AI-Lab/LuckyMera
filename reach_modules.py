from archetype_modules import ReachTask


class Gold(ReachTask):
    def __init__(self, dungeon_walker, game, task_name):
        super().__init__(dungeon_walker, game, task_name)

    def planning(self, stats, safe_play, agent):
        path, coords = self.standard_plan([(36, -1)], False, safe_play)
        if path is None or len(path) == 0:
            return None, None, None
        else:
            return self.name, path, coords


class Horizon(ReachTask):
    def __init__(self, dungeon_walker, game, task_name):
        super().__init__(dungeon_walker, game, task_name)

    def condition_horizon_obj(self, tile, args):
        glyph = args[0]
        char = glyph[0]
        # color = glyph[1]
        if self.game.get_char(tile[0], tile[1]) == char:  # and self.color_obs[tile[0]][tile[1]] == color: wip
            if self.game.is_near_glyph(tile[0], tile[1], (32, 0), 8) and self.game.is_unexplored(tile[0], tile[1]):
                return True
        return False

    def horizon_plan(self, glyph, safe_play):
        found, y, x = self.game.find(self.condition_horizon_obj, glyph)
        if found:
            path = self.dungeon_walker.path_finder(y, x, False, safe_play)
            self.game.update_memory(y, x)
            return path, (y, x)
        return None, (-1, -1)

    def planning(self, stats, safe_play, agent):
        path, coords = self.horizon_plan([(46, 7)], safe_play)
        if path is None:
            return None, None, None
        else:
            return self.name, path, coords


class Unseen(ReachTask):
    def __init__(self, dungeon_walker, game, task_name):
        super().__init__(dungeon_walker, game, task_name)

    def condition_unexplored_obj(self, tile, args):
        char = -1
        color = -1
        glyph = args[0]
        if glyph is not None:
            char = glyph[0]
            color = glyph[1]
        isolated = args[1]
        if self.game.get_memory(tile[0], tile[1]) == -1 and \
                (glyph is None and self.game.is_walkable(tile[0], tile[1])) or (
                char == self.game.get_char(tile[0], tile[1])
                and color == self.game.get_color(tile[0], tile[1])
                and (not isolated or self.game.is_isolated(tile[0], tile[1], glyph, True))):
            return True
        else:
            return False

    # metodo ausiliario per la ricerca e il pathfinding verso un obbiettivo inesplorato/isolato
    def unexplored_plan(self, glyph, not_reach_diag, isolated, safe_play):
        found, y, x = self.game.find(self.condition_unexplored_obj, [glyph, isolated])
        if found:
            path = self.dungeon_walker.path_finder(y, x, not_reach_diag, safe_play)
            self.game.update_memory(y, x)
            return path, (y, x)
        return None, (-1, -1)

    def planning(self, stats, safe_play, agent):
        path, coords = self.unexplored_plan(None, False, False, safe_play)
        if path is None or len(path) == 0:
            return None, None, None
        else:
            return self.name, path, coords
