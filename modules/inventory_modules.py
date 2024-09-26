import nle.nethack as nh
from modules.archetype_modules import Skill, InventorySkill

"""Get the probability that a random object in obj_probabilities is in the dangerous list"""
def risk(obj_probabilities, dangerous):
    return sum(p for o,p in obj_probabilities if o in dangerous)

"""To identify potions, the agent drinks them. Before drinking an unknown potion, check the probability that the potion is a potion of sickness or acid, so that if that probability is low, we may continue"""
class DrinkId(InventorySkill):
    def __init__(self, dungeon_walker, game, skill_name):
        super().__init__(dungeon_walker, game, skill_name)

    
    """ check for unidentified potions with low risk of danger """
    def item_planning(self, stats, safe_play, agent):
        ig = self.game.item_manager
        for i in self.game.get_items_by_class(nh.POTION_CLASS):
            item = ig.parse_item(self.game.inv_obs.descs[i])
            # get the id of the potion appearence
            id = nh.glyph_to_obj(self.game.inv_obs.glyphs[i])
            # update the probabilities on possible potion identities
            ig.can_be(id, item.possible_objects)
            if len(item.possible_objects) == 1:
                # already identified, skip
                continue
            # set the maximum acceptable risk
            r = 0.01 if safe_play else 0.1
            if item.count > 1 and item.buc_status != 'cursed' and item.cost == 0 and risk(ig.get_possible_objects(id), ["sickness", "acid"]) <= r:
                return i
        return -1

    """The planning already checked the safety, the agent can drink"""
    def execution(self, _, object_idx, agent, stats):
        self.game.do_it(nh.Command.QUAFF, [self.game.inv_obs.letters[object_idx]])

"""The agent check the AC(Armor Class) of any armor in his inventory. If there is armor that is convenient to wear (or switch to), wear it"""
class WearBestArmor(InventorySkill):
    def item_planning(self, stats, safe_play, agent):
        ig = self.game.item_manager
        equipment = {}
        candidates = {}
        for i in self.game.get_items_by_class(nh.ARMOR_CLASS):
            # has armor not worn
            item = ig.parse_item(self.game.inv_obs.descs[i])
            AC = item.attributes[0]
            cat = item.category
            (equipment if item.position == "on" else candidates)[cat] = (i, AC)
            # is in equipment and candidates, and equipment.ac < candidates.ac
            if cat in equipment and cat in candidates and equipment[cat][1] < candidates[cat][1]:
                return equipment[cat][0], candidates[cat][0]
        cat = list(set.difference(set(candidates), set(equipment)))
        # player already has best armor
        if len(cat) == 0:
            return -1
        # is only in candidates
        return None, candidates[cat[0]][0]
    """ object_indexes has two possible values:
    None, j: the agent has armor in the inventory at index j and can wear it directly
    i, j: the agent is wearing armor at index i, but should switch to j"""
    def execution(self, _, object_indexes, agent, stats):

        if object_indexes[0] is not None: # drop low quality armor
            self.game.do_it(nh.Command.TAKEOFF, [self.game.inv_obs.letters[object_indexes[0]]])
            self.game.do_it(nh.Command.DROP, [self.game.inv_obs.letters[object_indexes[0]]])
        # wear best armor
        self.game.do_it(nh.Command.WEAR, [self.game.inv_obs.letters[object_indexes[1]]])
        pass

# WIP do not use yet

class PetShowCurse(Skill):
    def __init__(self, dungeon_walker, game, skill_name):
        pass

    def item_planning(self, stats, safe_play, agent):
        # obj_letter = self.game.inv_get_unknown()
        if self.game.get_pet_alive() and \
           self.game.is_safe(*agent):
            return obj_letter

    def execution(self, path, arg1, agent, stats):
        # drop suspicious object on the floor(remember tile=x)
        # move to the farthest tile from pet adj to x until pet steps on x or receive "reluctant" or "picks up"
        # if "reluctant", ignore x
        # if pet steps on it, go to x and pick up
        # rew, done, info = self.game.do_it(action, None)
        # return rew, done, info
        pass


class IdWand(InventorySkill):
    def item_planning(self, stats, safe_play, agent):
        # ... game.get_items_by_class(nh.WAND_CLASS)
        # has unidentified wand
        pass

    def execution(self, path, arg1, agent, stats):
        # engrave with hands, then engrave with wand
        pass


class IdPrice(Skill):
    def item_planning(self, stats, safe_play, agent):
        # find unidentified scroll, potion and is in shop
        # return path to shop item
        pass

    def execution(self, path, arg1, agent, stats):
        # update possible item ids with buy price, after reaching the item
        pass


