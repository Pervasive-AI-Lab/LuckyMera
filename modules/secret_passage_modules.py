from modules.archetype_modules import HiddenSkill


class HiddenRoom(HiddenSkill):
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

        if 3 <= stats.hunger_state <= 4:
            return None, None, None
        path, coords = self.unsearched_plan([(46, 7)], safe_play)
        if path is None or len(path) == 0:
            return None, None, None
        else:
            return "search_hidden", path, coords


class HiddenCorridor(HiddenSkill):
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

        if 3 <= stats.hunger_state <= 4:
            return None, None, None
        path, coords = self.unsearched_plan([(35, 7)], safe_play)
        if path is None or len(path) == 0:
            return None, None, None
        else:
            return "search_hidden", path, coords
