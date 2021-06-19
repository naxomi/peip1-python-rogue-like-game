import copy
import math
import random

random.seed(2)


def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt (Windows') getch.
        import msvcrt
        return lambda: msvcrt.getch().decode('utf-8')
    # POSIX system. Create and return a getch that manipulates the tty.
    import sys
    import tty

    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch


def sign(x: int) -> int:
    if x > 0:
        return 1
    return -1


class Coord(object):
    """Implementation of a map coordinate"""

    def __init__(self, x: int, y: int) -> None:
        """
        Is a coordinate of the map
        :param x: x coordinate
        :param y: y coordinate
        """
        self.x = x
        self.y = y

    def __eq__(self, other: "Coord") -> bool:
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"<{str(self.x)},{str(self.y)}>"

    def __add__(self, other: "Coord") -> "Coord":
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Coord") -> "Coord":
        return Coord(self.x - other.x, self.y - other.y)

    def distance(self, other: "Coord") -> float:
        """Returns the distance between two coordinates."""
        d = self - other
        return math.sqrt(d.x * d.x + d.y * d.y)

    def direction(self, other: "Coord") -> "Coord":
        """Returns the direction between two coordinates."""
        cos45 = 1 / math.sqrt(2)

        d = self - other
        cos = d.x / self.distance(other)
        if cos > cos45:
            return Coord(-1, 0)
        elif cos < -cos45:
            return Coord(1, 0)
        elif d.y > 0:
            return Coord(0, -1)
        return Coord(0, 1)


class Element(object):
    """Base class for game elements. Have a name.
        Abstract class."""

    def __init__(self, name: str, abbreviation: str = "") -> None:
        self.name = name
        if abbreviation == "":
            abbreviation = name[0]
        self.abbreviation = abbreviation

    def __repr__(self) -> str:
        return self.abbreviation

    def description(self) -> str:
        """Description of the element"""
        return f"<{self.name}>"

    def meet(self, hero: "Hero") -> None:
        """Makes the hero meet an element. Not implemented. """
        raise NotImplementedError('Abstract Element')


class Creature(Element):
    """A creature that occupies the dungeon.
        Is an Element. Has hit points and strength."""

    defaultInventorySize = 10

    def __init__(self, name: str, hp: int, abbreviation: str = "", strength: int = 1, xp: int = 0,
                 weapon_slot: list = None, powers_list: list = None) -> None:
        super().__init__(name, abbreviation)
        self.hp = hp
        self.default_hp = hp
        self.strength = strength
        self.xp = xp

        if weapon_slot is not None:
            self.weapon_slot = weapon_slot
        else:
            self.weapon_slot = []

        if powers_list is not None:
            self.powers_list = powers_list
        else:
            self.powers_list = []

        # self._inventory = [Weapon("HUGE Sword", "T", usage=None, durability=100, damage=100)]
        self._inventory = []

    def description(self) -> str:
        """Description of the creature"""
        if self.hp > 0:
            return Element.description(self) + "(" + str(self.hp) + ")"
        return Element.description(self) + "(0)"

    def gain_xp(self, xp_point):
        raise NotImplementedError

    def meet(self, other: "Creature") -> bool:

        """The creature is encountered by an other creature.
            The other one hits the creature. Return True if the creature is dead."""

        self.hit(other)

        the_game().add_message("The " + other.name + " hits the " + self.description())
        if self.hp > 0:
            return False
        if isinstance(self, Creature) and not isinstance(self, Hero):
            other.gain_xp(self.xp)
        return True

    def hit(self, other: "Creature") -> None:

        if len(other.powers_list) != 0:
            for effect_infos_list in other.powers_list:
                effect_infos_list[0].add_effect(
                    effect_infos_list[0](the_game(), self, effect_infos_list[1], effect_infos_list[2]))

        if other.has_weapon() and other.has_an_hitting_weapon():
            self.hp -= other.current_weapon().damage
        else:
            self.hp -= other.strength

    def equip_weapon(self, weapon: "Weapon") -> None:
        if len(self.weapon_slot) != 0:
            self._inventory.append(self.weapon_slot[0])
            self.weapon_slot.clear()

        self.weapon_slot.append(weapon)
        self._inventory.remove(weapon)

    def remove_current_weapon(self) -> None:
        if self.current_weapon():
            if len(self._inventory) <= self.defaultInventorySize:
                self._inventory.append(self.current_weapon())
                self.weapon_slot.clear()
                the_game().add_message("You removed your weapon from it's slot")
            else:
                the_game().add_message("You don't have any space in your inventory to place your weapon")
        else:
            the_game().add_message("You currently don't have a weapon to remove from it's slot")

    def has_weapon(self) -> bool:
        if len(self.weapon_slot) >= 1:
            return True

    def current_weapon(self) -> bool or "Weapon":
        if self.has_weapon():
            return self.weapon_slot[0]
        else:
            return False

    def has_an_hitting_weapon(self):
        if self.current_weapon().weaponType == Weapon._weapon_type_list[0]:
            return True

    def has_a_throwing_weapon(self):
        if self.current_weapon().weaponType == Weapon._weapon_type_list[1]:
            return True

    def has_a_projectile_weapon(self):
        if self.current_weapon().weaponType == Weapon._weapon_type_list[2]:
            return True

    # def applyStuffEffects(self):
    #     return


class Hero(Creature):
    """The hero of the game.
        Is a creature. Has an inventory of elements. """

    defaultLevelSize = 25

    def __init__(self, name="Hero", hp=10, abbreviation="@", strength=2, level=1, xp=0, gold=0, stomach=10,
                 weapon_slot=None):
        Creature.__init__(self, name, hp, abbreviation, strength, xp, weapon_slot)

        self.xp = xp
        self.level = level
        self.gold = gold
        self.stomach = stomach
        self.default_stomach_size = stomach

    def description(self):
        """Description of the hero"""
        if len(self.weapon_slot) != 0:
            return Creature.description(self) + str(self._inventory) + " |" + str(self.current_weapon()) + "|"
        else:
            return Creature.description(self) + str(self._inventory)

    def full_description(self):
        """Complete description of the hero"""
        res = ''
        for e in self.__dict__:

            if e[0] != '_' and "default" not in e:
                if e == "xp":
                    res += '> ' + e + ' : ' + str(self.__dict__[e]) + "/" + str(
                        self.defaultLevelSize * self.level) + '\n'
                else:
                    res += '> ' + e + ' : ' + str(self.__dict__[e]) + '\n'
        res += '> INVENTORY : ' + str([x.name for x in self._inventory]) + '\n'
        res += '> Effects : ' + str(
            [f"{x.name}<{x.level}>({x.duration})" for x in the_game().active_effects if x.creature is self])

        if self.has_weapon():
            res += '> Weapon : ' + str(self.current_weapon().name)
        return res

    @staticmethod
    def check_equipment(o):
        """Check if o is an Equipment."""
        if not isinstance(o, Equipment):
            raise TypeError('Not a Equipment')

    def take(self, elem):
        """The hero takes adds the equipment to its inventory"""
        self.check_equipment(elem)
        if elem.name == "gold":
            self.gold += 1
        else:
            self._inventory.append(elem)

            if len(self._inventory) > Hero.defaultInventorySize:
                the_game().add_message("You don't have enough space in your inventory")

    def check_inventory_size(self):
        if len(self._inventory) > Hero.defaultInventorySize:
            while True:
                try:
                    self.delete_item(the_game().select(self._inventory))
                    break
                except:
                    print("Wrong value entered.")

    def use(self, elem):
        """Use a piece of equipment"""
        if elem is None:
            return
        self.check_equipment(elem)
        if elem not in self._inventory:
            raise ValueError('Equipment ' + elem.name + 'not in inventory')
        if elem.use(self):
            self._inventory.remove(elem)

    def delete_item(self, elem, throwing=False):
        """Delete an element from the inventory"""
        if len(self._inventory) > 0:
            if elem in self._inventory:
                self._inventory.remove(elem)
                if throwing:
                    the_game().add_message(f"You have successfully thrown the item : {elem.name}")
                else:
                    the_game().add_message(f"You have successfully deleted the item : {elem.name}")
            else:
                the_game().add_message("Could not find the item to delete. Maybe try with another value")

    def gain_xp(self, creature_xp):

        self.xp += creature_xp

        the_game().add_message("You gained {0} XP points".format(creature_xp))

        xp_to_use = self.xp
        level_steps = self.defaultLevelSize * self.level
        level_won = 0

        if xp_to_use > level_steps:
            while xp_to_use > level_steps:
                xp_to_use -= level_steps

                self.gain_level(1)

                level_steps = self.defaultLevelSize * self.level
                level_won += 1

            self.xp = xp_to_use
            the_game().add_message("You won {0} level(s) and are now level {1}".format(level_won, self.level))

    def gain_level(self, nb_of_level):
        self.level += 1
        self.strength += nb_of_level
        self.gold += nb_of_level + self.level

        the_game().add_message(
            "You now have a strength of {0} and won {1} gold coins".format(self.strength, self.level))

    def verify_stomach(self):
        if self.stomach == 0:
            self.__dict__["hp"] -= 1

    @staticmethod
    def choose_direction():
        print("Choose a direction to orientate yourself using the keys to move")

        c = getch()

        if c in Map.dir:
            return Map.dir[c]

        return False

    def throw_item(self, item, distance):

        if not isinstance(item, Equipment):
            return False

        hero_coord = the_game().floor.pos(self)
        direction = Hero.choose_direction()

        if not direction:
            return False

        item_coord = hero_coord + direction

        for i in range(distance):
            if i == 0:
                things_on_next_cell = the_game().floor.get(the_game().floor.pos(self) + direction)
            else:
                things_on_next_cell = the_game().floor.get(the_game().floor.pos(item) + direction)

            if isinstance(things_on_next_cell, Creature):
                item.use(things_on_next_cell, monster=True)
                if i != 0:
                    the_game().floor.rm(the_game().floor.pos(item))
                self.delete_item(item, True)
                break
            elif isinstance(things_on_next_cell, Equipment):
                if i != 0:
                    the_game().floor.rm(the_game().floor.pos(item))
                    self.delete_item(item, True)
                break
            elif things_on_next_cell != the_game().floor.ground:
                if i == 0:
                    the_game().add_message("You can't throw the item in this direction")
                break
            elif things_on_next_cell == the_game().floor.ground:
                if i == 0:
                    the_game().floor.put(item_coord, item)
                    if i == distance - 1:
                        self.delete_item(item, True)
                else:
                    the_game().floor.move(item, direction)
            else:
                raise NotImplementedError("WTF BRO")


class Effect(object):

    def __init__(self, game, creature):
        self.game = game
        self.creature = creature
        self.name = ""
        self.value = 0
        self.info = ""
        self.duration = None
        self.level = 0

    def delete(self):
        try:
            self.game.active_effects.remove(self)
            del self
        except ValueError:
            pass

    def update(self):
        self.action()

        if self.duration is not None:
            self.duration -= 1

            if self.duration <= 0:
                self.deactivate()
                return True

    def action(self):
        self.game.add_message(self.info)

    def add_effect(self):
        self.game.active_effects.append(self)

    def activate(self) -> None:
        self.action()
        if self not in self.game.active_effects:
            self.add_effect()

    def deactivate(self):
        self.game.add_message(self.info)
        self.delete()

    def clear(self, unique=True):
        effects_to_delete = []
        for effect in self.game.active_effects:
            if effect.creature is self.creature:
                effects_to_delete.append(effect)

        for effect in effects_to_delete:
            Effect.delete(effect)

        return unique


class EphemeralEffect(Effect):

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature)
        self.duration = duration
        self.level = level

    def activate(self, unique: bool = True) -> bool:
        super().activate()

        if self.duration is not None:
            self.duration -= 1

            if self.duration <= 0:
                self.deactivate()

        return unique

    def deactivate(self, kill: bool = False) -> None:
        if kill:
            self.info = f"[{self.creature.name}] has been killed by {self.name}<{self.level}>"
        else:
            self.info = f"\n[{self.creature.name}] {self.name} effect disappeared"
        super().deactivate()


class HealEffect(EphemeralEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "Recovering hp : +"

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature, duration, level)
        self.name = "Heal"
        self.value = self.level * HealEffect.LEVEL_FACTOR

    def action(self):
        if self.creature.default_hp > self.creature.hp + self.value:
            self.creature.hp += self.value
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {HealEffect.DESCRIPTION}{self.value}"

        else:
            self.creature.hp = self.creature.default_hp
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | Full Health : {self.creature.hp}/{self.creature.hp}"

        super().action()


class PoisonEffect(EphemeralEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "Losing hp : -"

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature, duration, level)
        self.name = "Poison"
        self.value = self.level * PoisonEffect.LEVEL_FACTOR

    def action(self):
        self.creature.hp -= self.value
        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {PoisonEffect.DESCRIPTION}{self.value}"

        if self.creature.hp == 0:
            self.game.floor.rm(self.game.floor.pos(self.creature))
            super().deactivate(True)
        else:
            super().action()


class FeedEffect(EphemeralEffect):
    """
    Effect used to feed the hero. Creatures don't have a stomach so they can't be applied this effect.
    """
    LEVEL_FACTOR = 1
    DESCRIPTION = "I'm eating : +"

    def __init__(self, game, creature, duration, level):

        if not isinstance(creature, Hero):
            raise TypeError("The creature for this effect must be a hero.")

        super().__init__(game, creature, duration, level)
        self.name = "Feed"
        self.value = self.level * FeedEffect.LEVEL_FACTOR

    def action(self) -> None:
        if self.creature.default_stomach_size > self.creature.stomach + self.value:
            self.creature.stomach += self.value
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {FeedEffect.DESCRIPTION}{self.value}"

        else:
            self.creature.hp = self.creature.default_hp
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | Max food : {self.creature.stomach}/{self.creature.stomach}"

        super().action()


class HungerEffect(EphemeralEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "I'm hungry : -"

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature, duration, level)
        self.name = "Hunger"
        self.value = self.level * HungerEffect.LEVEL_FACTOR

    def action(self):
        if isinstance(self.creature, Hero):
            self.creature.stomach -= self.value
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {HungerEffect.DESCRIPTION}{self.value}"
            super().action()


class TeleportEffect(EphemeralEffect):  # IS AN INSTANT EFFECT

    DESCRIPTION = "You have been teleported"

    def __init__(self, game, creature, duration=1):
        super().__init__(game, creature, duration, 0)
        self.name = "Teleportation"

    def action(self):
        """Teleport the creature"""
        r = self.game.floor.rand_room()
        c = r.rand_coord()

        while not self.game.floor.get(c) == Map.ground:
            c = r.rand_coord()
        self.game.floor.rm(self.game.floor.pos(self.creature))
        self.game.floor.put(c, self.creature)

        self.info = f"The creature <{self.creature.name}> has been teleported"


# CONSTANT EFFECTS
'''
class ConstantEffect(Effect):

    def __init__(self, game, creature):
        super().__init__(game, creature)
        self.hasBeenActivated = False

    def activate(self):
        if not self.hasBeenActivated:
            super().activate()
            self.hasBeenActivated = True


class StrengthEffect(ConstantEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION_ACTIVATE = "I feel stronger : +"
    DESCRIPTION_DEACTIVATE = "- End of boost - I feel weaker... : -"

    def __init__(self, game, creature, duration=None, level=1):
        super().__init__(game, creature)
        self.name = "Strength"
        self.duration = duration
        self.level = level
        self.value = self.level * StrengthEffect.LEVEL_FACTOR

    def action(self):
        self.creature.strength += self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {StrengthEffect.DESCRIPTION_ACTIVATE}{self.value}"
        super().action()

    def activate(self):
        super().activate()

    def deactivate(self):
        self.creature.strength -= self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {StrengthEffect.DESCRIPTION_DEACTIVATE}{self.value}"
        super().deactivate()


class WeaknessEffect(ConstantEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION_ACTIVATE = "I feel weaker : +"
    DESCRIPTION_DEACTIVATE = "- End of malus - I feel stronger... : -"

    def __init__(self, game, creature, duration, level):
        super().__init__(self, game, creature)
        self.name = "Weakness"
        self.duration = duration
        self.level = level
        self.value = self.level * WeaknessEffect.LEVEL_FACTOR

    def activate(self):
        self.creature.strength -= self.value

        if not self.hasBeenActivated:
            self.game.activeEffects.append(self)
            self.hasBeenActivated = True

        if isinstance(self.creature, Hero):
            self.info = f"{self.name}<{self.level}> | {WeaknessEffect.DESCRIPTION_ACTIVATE}{self.value}"

    def deactivate(self):
        self.creature.strength += self.value

        if isinstance(self.creature, Hero):
            self.info = f"{self.name}<{self.level}> | {WeaknessEffect.DESCRIPTION_DEACTIVATE}{self.value}"

        super().deactivate()
'''


# EQUIPMENT
class Equipment(Element):
    """A piece of equipment"""

    def __init__(self, name, abbreviation="", usage=None, durability=None):
        Element.__init__(self, name, abbreviation)
        self.usage = usage
        self.durability = durability

    def meet(self, hero):
        """Makes the hero meet an element. The hero takes the element."""
        hero.take(self)
        the_game().add_message("You pick up a " + self.name)
        return True

    def use(self, creature, monster=False):
        """Uses the piece of equipment. Has effect on the hero according usage.
            Return True if the object is consumed."""
        if self.usage is None:
            if not monster:
                the_game().add_message(f"The {creature.name} can't use the item {self.name}")
            return False

        else:
            the_game().add_message(f"The {creature.name} uses the item {self.name}")
            return self.usage(self, creature)

    # def isDurabilityValid(self):
    #     if self.durability == 0:
    #         return False
    #     return True


class Weapon(Equipment):
    """A weapon which can be used by the Hero or the monsters"""

    _weapon_type_list = ["hit", "throw", "projectile"]

    def __init__(self, name, abbreviation="", weapon_type=_weapon_type_list[0], usage=None, effects_list=None, damage=1,
                 durability=10):
        Equipment.__init__(self, name, abbreviation, usage, durability)
        self.weaponType = weapon_type

        if effects_list is not None:
            self.effectsList = effects_list  # effects applied to the creature being hit
        else:
            self.effectsList = []

        self.damage = damage

    def apply_weapon_effects(self, creature):
        for effect in self.effectsList:
            creature.add_effect(effect, True)

    def throw(self, distance):
        return

    def launch_projectile(self, distance, projectile_to_use):
        return


class Projectile(object):
    "Class to define the behaviour of projectiles"


class Amulet(Equipment):

    def __init__(self, name, abbreviation="", usage=None, durability=None):
        Equipment.__init__(self, name, abbreviation, usage, durability)


class Room(object):
    """A rectangular room in the map"""

    def __init__(self, c1, c2):
        self.c1 = c1
        self.c2 = c2

    def __repr__(self):
        return "[" + str(self.c1) + ", " + str(self.c2) + "]"

    def __contains__(self, coord):
        return self.c1.x <= coord.x <= self.c2.x and self.c1.y <= coord.y <= self.c2.y

    def intersect(self, other):
        """Test if the room has an intersection with another room"""
        sc3 = Coord(self.c2.x, self.c1.y)
        sc4 = Coord(self.c1.x, self.c2.y)
        return self.c1 in other or self.c2 in other or sc3 in other or sc4 in other or other.c1 in self

    def center(self):
        """Returns the coordinates of the room center"""
        return Coord((self.c1.x + self.c2.x) // 2, (self.c1.y + self.c2.y) // 2)

    def rand_coord(self):
        """A random coordinate inside the room"""
        return Coord(random.randint(self.c1.x, self.c2.x), random.randint(self.c1.y, self.c2.y))

    def rand_empty_coord(self, map):
        """A random coordinate inside the room which is free on the map."""
        c = self.rand_coord()
        while map.get(c) != Map.ground or c == self.center():
            c = self.rand_coord()
        return c

    def decorate(self, map):
        """Decorates the room by adding a random equipment and monster."""
        map.put(self.rand_empty_coord(map), the_game().rand_equipment())
        map.put(self.rand_empty_coord(map), the_game().rand_monster())


class Map(object):
    """A map of a game floor.
        Contains game elements."""

    ground = '.'  # A walkable ground cell
    dir = {'z': Coord(0, -1),
           'x': Coord(0, 1),
           'd': Coord(1, 0),
           'q': Coord(-1, 0),
           'a': Coord(-1, -1),
           'e': Coord(1, -1),
           'w': Coord(-1, 1),
           'c': Coord(1, 1),
           }

    empty = ' '  # A non walkable cell

    def __init__(self, size=20, hero=None):
        self._mat = []
        self._elem = {}
        self._rooms = []
        self._roomsToReach = []

        for i in range(size):
            self._mat.append([Map.empty] * size)
        if hero is None:
            hero = Hero()
        self.hero = hero
        self.generate_rooms(7)
        self.reach_all_rooms()
        self.put(self._rooms[0].center(), hero)
        for r in self._rooms:
            r.decorate(self)

    def add_room(self, room):
        """Adds a room in the map."""
        self._roomsToReach.append(room)
        for y in range(room.c1.y, room.c2.y + 1):
            for x in range(room.c1.x, room.c2.x + 1):
                self._mat[y][x] = Map.ground

    def find_room(self, coord):
        """If the coord belongs to a room, returns the room elsewhere returns None"""
        for r in self._roomsToReach:
            if coord in r:
                return r
        return None

    def intersect_none(self, room):
        """Tests if the room shall intersect any room already in the map."""
        for r in self._roomsToReach:
            if room.intersect(r):
                return False
        return True

    def dig(self, coord):
        """Puts a ground cell at the given coord.
            If the coord corresponds to a room, considers the room reached."""
        self._mat[coord.y][coord.x] = Map.ground
        r = self.find_room(coord)
        if r:
            self._roomsToReach.remove(r)
            self._rooms.append(r)

    def corridor(self, cursor, end):
        """Digs a corridors from the coordinates cursor to the end, first vertically, then horizontally."""
        d = end - cursor
        self.dig(cursor)
        while cursor.y != end.y:
            cursor = cursor + Coord(0, sign(d.y))
            self.dig(cursor)
        while cursor.x != end.x:
            cursor = cursor + Coord(sign(d.x), 0)
            self.dig(cursor)

    def reach(self):
        """Makes more rooms reachable.
            Start from one random reached room, and dig a corridor to an unreached room."""
        roomA = random.choice(self._rooms)
        roomB = random.choice(self._roomsToReach)

        self.corridor(roomA.center(), roomB.center())

    def reach_all_rooms(self):
        """Makes all rooms reachable.
            Start from the first room, repeats @reach until all rooms are reached."""
        self._rooms.append(self._roomsToReach.pop(0))
        while len(self._roomsToReach) > 0:
            self.reach()

    def rand_room(self):
        """A random room to be put on the map."""
        c1 = Coord(random.randint(0, len(self) - 3), random.randint(0, len(self) - 3))
        c2 = Coord(min(c1.x + random.randint(3, 8), len(self) - 1), min(c1.y + random.randint(3, 8), len(self) - 1))
        return Room(c1, c2)

    def generate_rooms(self, n):
        """Generates n random rooms and adds them if non-intersecting."""
        for i in range(n):
            r = self.rand_room()
            if self.intersect_none(r):
                self.add_room(r)

    def __len__(self):
        return len(self._mat)

    def __contains__(self, item):
        if isinstance(item, Coord):
            return 0 <= item.x < len(self) and 0 <= item.y < len(self)
        return item in self._elem

    def __repr__(self):
        s = ""
        for i in self._mat:
            for j in i:
                s += str(j)
            s += '\n'
        return s

    def check_coord(self, c):
        """Check if the coordinates c is valid in the map."""
        if not isinstance(c, Coord):
            raise TypeError('Not a Coord')
        if not c in self:
            raise IndexError('Out of map coord')

    @staticmethod
    def check_element(o):
        """Check if o is an Element."""
        if not isinstance(o, Element):
            raise TypeError('Not a Element')

    def put(self, c, o):
        """Puts an element o on the cell c"""
        self.check_coord(c)
        self.check_element(o)
        if self._mat[c.y][c.x] != Map.ground:
            raise ValueError('Incorrect cell')
        if o in self._elem:
            raise KeyError('Already placed')
        self._mat[c.y][c.x] = o
        self._elem[o] = c

    def get(self, c):
        """Returns the object present on the cell c"""
        self.check_coord(c)
        return self._mat[c.y][c.x]

    def pos(self, o):
        """Returns the coordinates of an element in the map """
        self.check_element(o)
        return self._elem[o]

    def rm(self, c):
        """Removes the element at the coordinates c"""
        self.check_coord(c)
        del self._elem[self._mat[c.y][c.x]]
        self._mat[c.y][c.x] = Map.ground

    def move(self, e, way):
        """Moves the element e in the direction way."""
        orig = self.pos(e)
        dest = orig + way
        if dest in self:
            if self.get(dest) == Map.ground:
                self._mat[orig.y][orig.x] = Map.ground
                self._mat[dest.y][dest.x] = e
                self._elem[e] = dest
            elif self.get(dest) != Map.empty and self.get(dest).meet(e) and self.get(dest) != self.hero:
                self.rm(dest)

    def move_all_monsters(self):
        """Moves all monsters in the map.
            If a monster is at distance lower than 6 from the hero, the monster advances."""
        h = self.pos(self.hero)
        for e in self._elem:
            c = self.pos(e)
            if isinstance(e, Creature) and e != self.hero and c.distance(h) < 6:
                d = c.direction(h)
                if self.get(c + d) in [Map.ground, self.hero]:
                    self.move(e, d)


class Game(object):
    """ Class representing game state """

    """ available equipments """
    equipments = {0: [Equipment("gold", "o"),
                      Equipment("potion heal", "!",
                                usage=lambda self, hero: HealEffect.activate(HealEffect(the_game(), hero, 1, 3))),
                      Equipment("basic bread", "§", usage=lambda self, hero: FeedEffect.activate(
                          FeedEffect(the_game(), hero, 1, hero.default_stomach_size))),
                      Equipment("hunger mushroom", "£",
                                usage=lambda self, hero: HungerEffect.activate(HungerEffect(the_game(), hero, 3, 1))),
                      Equipment("poisonous mushroom", "%",
                                usage=lambda self, hero: PoisonEffect.activate(PoisonEffect(the_game(), hero, 3, 1))),
                      ],
                  1: [Equipment("potion teleport", "!",
                                usage=lambda self, hero: TeleportEffect.activate(TeleportEffect(the_game(), hero))),
                      ],
                  2: [Equipment("milk", "m", usage=lambda self, hero: Effect.clear(Effect(the_game(), hero))),
                      ],
                  3: [Equipment("portoloin", "w",
                                usage=lambda self, hero: TeleportEffect.activate(TeleportEffect(the_game(), hero),
                                                                                 False)),
                      ],
                  }

    """ available weapons """
    weapons = {
        0: [Weapon("Basic Sword", "†", weapon_type=Weapon._weapon_type_list[0], usage=None, damage=3, durability=10)],
        1: [],
        2: [],
    }

    """ available monsters """
    monsters = {0: [Creature("Goblin", hp=4, xp=4),
                    Creature("Bat", hp=2, abbreviation="W", xp=2)],
                1: [Creature("Ork", hp=6, strength=2, xp=10),
                    Creature("Blob", hp=10, xp=8)],
                3: [Creature("Poisonous spider", hp=5, xp=10, strength=0, abbreviation="&",
                             powers_list=[[PoisonEffect, 2, 1]])],
                5: [Creature("Dragon", hp=20, strength=3, xp=100)],
                }

    """ available actions """
    _actions = {'z': lambda h: the_game().floor.move(h, Coord(0, -1)),
                'q': lambda h: the_game().floor.move(h, Coord(-1, 0)),
                'x': lambda h: the_game().floor.move(h, Coord(0, 1)),
                'd': lambda h: the_game().floor.move(h, Coord(1, 0)),
                'a': lambda h: the_game().floor.move(h, Coord(-1, -1)),
                'e': lambda h: the_game().floor.move(h, Coord(1, -1)),
                'w': lambda h: the_game().floor.move(h, Coord(-1, 1)),
                'c': lambda h: the_game().floor.move(h, Coord(1, 1)),

                'i': lambda h: the_game().add_message(h.full_description()),
                'k': lambda h: h.__setattr__('hp', 0),
                'u': lambda h: h.use(the_game().select(h._inventory)),
                ' ': lambda h: None,
                'h': lambda hero: the_game().add_message("Actions available : " + str(list(Game._actions.keys()))),
                't': lambda hero: hero.delete_item(
                    the_game().select_item_to_del(hero._inventory) if len(hero._inventory) > 0 else False),
                'b': lambda hero: hero.equip_weapon(the_game().select_weapon(hero._inventory)) if any(
                    isinstance(elem, Weapon) for elem in hero._inventory) else the_game().add_message(
                    "You don't have any weapon in your inventory"),
                'n': lambda hero: hero.remove_current_weapon(),
                'l': lambda hero: hero.throw_item(the_game().select(hero._inventory), 5)

                }

    def __init__(self, level=1, _message=None, hero=None, floor=None, number_of_round=0):

        self.level = level
        self.active_effects = []

        if hero is None:
            hero = Hero()

        self.hero = hero

        if _message:
            self._message = _message
        else:
            self._message = []

        if floor:
            self.floor = floor
        else:
            self.floor = None

        self.number_of_round = number_of_round

    def build_floor(self):
        """Creates a map for the current floor."""
        self.floor = Map(hero=self.hero)

    def add_message(self, msg):
        """Adds a message in the message list."""
        self._message.append(msg)

    def read_messages(self):
        """Returns the message list and clears it."""
        s = ''
        for m in self._message:
            s += m + ".\n"
        self._message.clear()
        return s

    def rand_element(self, collect):
        """Returns a clone of random element from a collection using exponential random law."""
        x = random.expovariate(1 / self.level)
        for k in collect.keys():
            if k <= x:
                element_list = collect[k]
        return copy.copy(random.choice(element_list))

    def rand_equipment(self):
        """Returns a random equipment."""
        return self.rand_element(Game.equipments)

    def rand_monster(self):
        """Returns a random monster."""
        return self.rand_element(Game.monsters)

    @staticmethod
    def select(items_list: list) -> Element:

        print("Choose an item> " + str([str(items_list.index(e)) + ": " + e.name for e in items_list]))

        c = getch()

        if c.isdigit() and int(c) in range(len(items_list)):
            return items_list[int(c)]

    @staticmethod
    def select_item_to_del(items_list: list) -> Element:

        print("Choose an item to delete> " + str([str(items_list.index(e)) + ": " + e.name for e in items_list]))

        c = getch()

        if c.isdigit() and int(c) in range(len(items_list)) and len(items_list) != 0:
            return items_list[int(c)]

    @staticmethod
    def select_weapon(element_list):

        list_weapon = [e for e in element_list if isinstance(e, Weapon)]

        print("Choose a weapon> " + str([str(list_weapon.index(e)) + ": " + e.name for e in list_weapon]))

        c = getch()

        if c.isdigit() and int(c) in range(len(list_weapon)) and len(list_weapon) != 0:
            return list_weapon[int(c)]

    def play(self):

        """Main game loop"""

        self.build_floor()

        print("--- Welcome Hero! ---")

        while self.hero.hp > 0:

            print()
            print(self.floor)
            print(self.hero.description())
            print(self.read_messages())

            self.hero.check_inventory_size()

            print(self.read_messages())

            c = getch()
            if c in Game._actions:
                Game._actions[c](self.hero)

                if c in {"a", "z", "e", "q", "d", "w", "x", "c"}:

                    self.floor.move_all_monsters()
                    self.number_of_round += 1

                    if self.number_of_round % 20 == 0 and self.hero.stomach > 0:
                        self.hero.stomach -= 1

                    self.hero.verify_stomach()

                    if len(self.active_effects) != 0:
                        i = 0
                        while i < len(self.active_effects):
                            if not self.active_effects[i].update():
                                i += 1

        print("--- Game Over ---")


def the_game(game=Game()):
    return game


getch = _find_getch()
the_game().play()
