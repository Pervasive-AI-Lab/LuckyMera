from pyswip import Prolog
from game_items.stochastic_matrix import Stochastic_matrix
from collections import namedtuple
Item = namedtuple("Item", ["possible_objects", "category", "count", "buc_status", "enchantment", "charges", "lit", "position", "cost", "greased", "poisoned", "erosion", "proofed", "partial", "called", "named", "contents", "attributes"])

class Item_manager_sk:
    """Manages all items in a Nethack game.
    An item is an object(that may be unknown at the start of the game),
    has an appearence(that is what we see),
    a text description(used to describe the item in game),
    some attributes(may vary between different objects).
    Some objects have a random appearence(https://nethackwiki.com/wiki/Randomized_appearance),
    that is why the class stores a probability matrix for every kind of objects that share the possible random appearences.
    All the data for objects, appearences and items attributes is gathered from prolog_file
    """
    def __init__(self, prolog_file):
        """Consult prolog_file and initialize all the probability matrix, with the range of appearences associated with the matrix"""
        self.prolog = Prolog()
        rnd_objects_by_category = {}
        self.prolog.consult(prolog_file)
        for res in self.prolog.query("rnd_range(RND, MIN-MAX), object_type(CATEGORY, NAME, ABOUNDANCE, _, _, _, RND, _)"):
            category, obj, min_app, max_app, abd = res["CATEGORY"], res["NAME"], res["MIN"], res["MAX"], res["ABOUNDANCE"]
            if category not in rnd_objects_by_category:
                rnd_objects_by_category[category] = (min_app, max_app, [], [])
            rnd_objects_by_category[category][2].append(obj.decode())
            rnd_objects_by_category[category][3].append(abd)

        self.appearence_ranges = []
        self.matrices = []
        for (min_app, max_app, objs, abds) in rnd_objects_by_category.values():
            self.appearence_ranges.append((min_app, max_app))
            self.matrices.append(Stochastic_matrix(objs, abds))

    def get_stochastic(self, appearence):
        """Select and return one of the probability matrix by the given appearence"""
        for (i, (min_app, max_app)) in enumerate(self.appearence_ranges):
            if min_app <= appearence <= max_app:
                return self.matrices[i]
        return None

    def found(self, appearence):
        """Found an object with given appearence.
        The manager must update the corresponding matrix"""
        mat = self.get_stochastic(appearence)
        if mat is not None:
            mat.found(appearence)
            return True
        return False

    def is_not(self, appearence, obj):
        """Found that an object can't have the given appearence.
        The manager must update the corresponding matrix"""
        mat = self.get_stochastic(appearence)
        if mat is not None:
            mat.is_not(appearence, obj)
            return True
        return False

    def can_be(self, appearence, objects):
        """Found that the object possibilities of the given appearence can be restricted to the given list of objects.
        The manager must update the corresponding matrix"""
        mat = self.get_stochastic(appearence)
        if mat is not None:
            # objects and mat.objects must have at least one object in common
            assert any(o in objects for o in mat.objects), objects
            for o in mat.objects:
                if o not in objects:
                    mat.is_not(appearence, o)
            return True
        return False

    def get_possible_objects(self, appearence):
        """Return a list of pairs (p, object) such that object has p probability to have the given appearence.
        If the given appearence is one of the many randomized appearences, use the associated probability matrix,
        otherwise, query prolog_file"""
        mat = self.get_stochastic(appearence)
        if mat is not None:
            (bis, i) = mat.get_bistochastic(10000, 1e-6)
            # print(i)
            if bis is not None:
                return mat.get_possible_objects(bis, appearence)
            return None
        possibilities = [[res["ABOUNDANCE"], res["NAME"].decode()] for res in
                         self.prolog.query(f"object(_, NAME, ABOUNDANCE, _ ,_, _, {appearence}, _)")]
        assert len(possibilities), appearence
        sum_abd = sum(p[0] for p in possibilities)
        for p in possibilities:
            p[0] /= sum_abd
        return sorted(possibilities, reverse=True)

    def parse_item(self, item_desc, charisma = "_"):
        """Parse the given item description, eventually taking in consideration charisma to have an accurate price identification"""
        item_desc = bytes(item_desc).decode().strip('\0')
        res = list(self.prolog.query(f"phrase(item_desc(N, BUC, GREASED, POIS, EROSION, PROOF, PART, ENCH, CATEGORY, NAME, CALL, NAMED, CONT, CHARGES, LIT, POS, COST, {charisma}, _, ATTRIBUTES), `{item_desc}`)"))
        assert len(res), f"can't parse: {item_desc}"
        return Item(
            set(r["NAME"].decode() for r in res), # possible objects this item can be
            res[0]["CATEGORY"], # item category
            res[0]["N"], # number of items in stack
            res[0]["BUC"], # curse/bless status
            res[0]["ENCH"], # enchantment
            res[0]["CHARGES"], # charges
            res[0]["LIT"], # is it lit?
            res[0]["POS"], # item position (wielded, in hands, offhand, in hand...)
            res[0]["COST"], # item cost, when in shop
            res[0]["GREASED"], # has the item been greased?
            res[0]["POIS"], # has the item been poisoned?
            res[0]["EROSION"], # is the item eroded?
            res[0]["PROOF"], # has the item been proofed? (fireproof, waterproof...)
            res[0]["PART"], # is the item diluted or partly eaten?
            res[0]["CALL"], # how it is called
            res[0]["NAMED"], # how it is named
            res[0]["CONT"], # how many items contains, if item is a container
            res[0]["ATTRIBUTES"]) # other attributes (AC, magic_cancellation) for armor, (skill, hit_bonus, damage2smallmonsters, damage2largemonsters) for weapon/projectiles
