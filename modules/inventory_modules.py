import nle.nethack as nh
from modules.archetype_modules import Skill
# WIP do not use yet


class PetShowCurse(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        return 0

    def planning(self, stats, safe_play, agent):
        obj_letter = self.game.inv_filter()[0][0]
        if self.game.get_pet_alive() and \
           self.game.is_safe(*agent):
            return self.name, None, obj_letter

    def execution(self, path, arg1, agent, stats):
        # drop suspicious object on the floor(remember tile=x)
        # move to the farthest tile from pet adj to x until pet steps on x or receive "reluctant" or "picks up"
        # if "reluctant", ignore x
        # if pet steps on it, go to x and pick up
        # rew, done, info = self.game.do_it(action, None)
        # return rew, done, info
        pass


class AltarShowCurse(Skill):
    def planning(self, stats, safe_play, agent):
        path, (y, x) = self.standard_plan(b'_', False, safe_play)
        # altar on map and has items with unknown curse
        # returns path to altar

    def execution(self, path, arg1, agent, stats):
        # travel to altar and drop all unknown stuff
        # pick up only uncursed
        pass


class IdWand(Skill):
    def planning(self, stats, safe_play, agent):
        # wand = game.get_item_by_class(nh.WAND_CLASS)
        # has unidentified wand
        pass

    def execution(self, path, arg1, agent, stats):
        # engrave with hands, then engrave with wand
        pass


class IdPrice(Skill):
    def planning(self, stats, safe_play, agent):
        # has unidentified scroll, potion and is in shop
        pass

    def execution(self, path, arg1, agent, stats):
        # tell shopkeeper you want to sell, get price, match with price range to id
        pass


class WearBestArmor(Skill):
    def planning(self, stats, safe_play, agent):
        # has armor not worn
        pass

    def execution(self, path, arg1, agent, stats):
        # wear best armor, drop low quality armor
        pass
