#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 21:13:57 2021

@author: raphaelanjou
"""

import copy
import math
import random
import copy

# from enums import Enum
# import os
# import pickle

random.seed(1)

import json


# class EffectType(Enum):
#     EPHEMERE = 0
#     CONSTANT = 1


def _find_getch():
    """Single char input, only works only on mac/linux/windows OS terminals"""
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return lambda: msvcrt.getch().decode('utf-8')
    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
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


def sign(x):
    if x > 0:
        return 1
    return -1


class Coord(object):
    """Implementation of a map coordinate"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return '<' + str(self.x) + ',' + str(self.y) + '>'

    def __add__(self, other):
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coord(self.x - other.x, self.y - other.y)

    def distance(self, other):
        """Returns the distance between two coordinates."""
        d = self - other
        return math.sqrt(d.x * d.x + d.y * d.y)

    def direction(self, other):
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

    def __init__(self, name, abbrv=""):
        self.name = name
        if abbrv == "":
            abbrv = name[0]
        self.abbrv = abbrv

    def __repr__(self):
        return self.abbrv

    def description(self):
        """Description of the element"""
        return "<" + self.name + ">"

    def meet(self, hero):
        """Makes the hero meet an element. Not implemented. """
        raise NotImplementedError('Abstract Element')


class Creature(Element):
    """A creature that occupies the dungeon.
        Is an Element. Has hit points and strength."""

    defaultInventorySize = 10

    def __init__(self, name, hp, abbrv="", strength=1, xp=1, weaponSlot=None):
        Element.__init__(self, name, abbrv)
        self.hp = hp
        self._defaultHp = hp
        self.strength = strength
        self.xp = xp

        if weaponSlot != None:
            self.weaponSlot = weaponSlot
        else:
            self.weaponSlot = []

        # self._inventory = [Weapon("HUGE Sword", "T", usage=None, durability=100, damage=100)]
        self._inventory = []

        self._ephemereEffects = {}
        self._constantEffectsToApply = {}
        self._constantEffectsApplied = {}

    def description(self):
        """Description of the creature"""
        if self.hp > 0:
            return Element.description(self) + "(" + str(self.hp) + ")"
        return Element.description(self) + "(0)"

    def meet(self, other):
        """The creature is encountered by an other creature.
            The other one hits the creature. Return True if the creature is dead."""

        self.hit(other)

        theGame().addMessage("The " + other.name + " hits the " + self.description())
        if self.hp > 0:
            return False
        if isinstance(self, Creature) and not isinstance(self, Hero):
            other.gainXP(self.xp)
        return True

    def hit(self, other):

        if other.hasWeapon() and other.hasAnHittingWeapon():
            self.hp -= other.currentWeapon().damage
        else:
            self.hp -= other.strength

    def addEffect(self, effect, unique=True):
        """The hero now has a new effect, maybe after using a potion or being attacked"""

        effect.effectFunc(self, effect.value)

        # theGame().addMessage("----------------\n")
        # theGame().addMessage(f"{object.__repr__(self)}, {self.name}\n")
        # theGame().addMessage("----------------\n")

        effect = copy.copy(effect)
        if effect.effectType == "constant":
            self._constantEffectsApplied[effect] = [None, effect.value]

        elif effect.effectType == "ephemere" and effect.duration != 1:
            self._ephemereEffects[effect] = [effect.duration - 1, effect.value]

        return unique

    def removeConstantEffect(self, effect):
        effect.power(self, -self._constantEffects[effect][1])

        if effect in self._constantEffectsApplied:
            del self._constantEffectsApplied[effect]
        elif effect in self._constantEffectsToApply:
            del self._constantEffectsToApply[effect]

    def removeEphemereEffect(self, effect):
        del self._ephemereEffects[effect]

    """ Is used to remove all the effects (constant, ephemere, instant) """

    def removeAllEffects(self, unique=True):
        self._ephemereEffects.clear()
        self._constantEffectsToApply.clear()

        # Invert the constant effects before removing them

        for effect in self._constantEffectsApplied.keys():
            effect.effectFunc(self, -self._constantEffectsApplied[effect][1])

        self._constantEffectsApplied.clear()

        return unique

    def applyAllEffects(self):

        # Appliquer les effets ephemere
        ephemereEffectsToDel = []

        for effect in self._ephemereEffects.keys():
            effect.effectFunc(self, self._ephemereEffects[effect][1])

            self._ephemereEffects[effect][0] -= 1

            if self._ephemereEffects[effect][0] == 0:
                ephemereEffectsToDel.append(effect)

        for ephemereEffectToDel in ephemereEffectsToDel:
            del self._ephemereEffects[ephemereEffectToDel]

        # Appliquer les effets constants
        for effect in self._constantEffectsToApply.keys():
            effect.effectFunc(self, self._constantEffectsToApply[effect][1])

        self._constantEffectsApplied.update(self._constantEffectsToApply)
        self._constantEffectsToApply.clear()

    def equipWeapon(self, weapon):
        if len(self.weaponSlot) != 0:
            self._inventory.append(self.weaponSlot[0])
            self.weaponSlot.clear()

        self.weaponSlot.append(weapon)
        self._inventory.remove(weapon)

    def removeCurrentWeapon(self):
        if self.currentWeapon() != False:
            if len(self._inventory) <= self.defaultInventorySize:
                self._inventory.append(self.currentWeapon())
                self.weaponSlot.clear()
                theGame().addMessage("You removed your weapon from it's slot")
            else:
                theGame().addMessage("You don't have any space in your inventory to place your weapon")
        else:
            theGame().addMessage("You currently don't have a weapon to remove from it's slot")

    def hasWeapon(self):
        if len(self.weaponSlot) >= 1:
            return True

    def currentWeapon(self):
        if self.hasWeapon():
            return self.weaponSlot[0]
        else:
            return False

    def hasAnHittingWeapon(self):
        if self.currentWeapon().weaponType == Weapon._weaponTypeList[0]:
            return True

    def hasAThrowingWeapon(self):
        if self.currentWeapon().weaponType == Weapon._weaponTypeList[1]:
            return True

    def hasAProjectileWeapon(self):
        if self.currentWeapon().weaponType == Weapon._weaponTypeList[2]:
            return True

    # def applyStuffEffects(self):
    #     return


class Hero(Creature):
    """The hero of the game.
        Is a creature. Has an inventory of elements. """

    defaultLevelSize = 25

    def __init__(self, name="Hero", hp=10, abbrv="@", strength=2, level=1, xp=0, gold=0, stomach=10, weaponSlot=None):
        Creature.__init__(self, name, hp, abbrv, strength, weaponSlot)

        self.xp = xp
        self.level = level
        self.gold = gold
        self.stomach = stomach
        self._defaultStomachSize = stomach

    def description(self):
        """Description of the hero"""
        if len(self.weaponSlot) != 0:
            return Creature.description(self) + str(self._inventory) + " |" + str(self.currentWeapon()) + "|"
        else:
            return Creature.description(self) + str(self._inventory)

    def fullDescription(self):
        """Complete description of the hero"""
        res = ''
        for e in self.__dict__:

            if e[0] != '_':
                if e == "xp":
                    res += '> ' + e + ' : ' + str(self.__dict__[e]) + "/" + str(
                        self.defaultLevelSize * self.level) + '\n'
                else:
                    res += '> ' + e + ' : ' + str(self.__dict__[e]) + '\n'
        res += '> INVENTORY : ' + str([x.name for x in self._inventory]) + '\n'
        res += '> Effects : ' + str([x.name for x in theGame().activeEffects if x.creature is self])

        if self.hasWeapon():
            res += '> Weapon : ' + str(self.currentWeapon().name)
        return res

    def checkEquipment(self, o):
        """Check if o is an Equipment."""
        if not isinstance(o, Equipment):
            raise TypeError('Not a Equipment')

    def take(self, elem):
        """The hero takes adds the equipment to its inventory"""
        self.checkEquipment(elem)
        if elem.name == "gold":
            self.gold += 1
        else:
            self._inventory.append(elem)

            if len(self._inventory) > Hero.defaultInventorySize:
                theGame().addMessage("You don't have enough space in your inventory")

    def checkInventorySize(self):
        if len(self._inventory) > Hero.defaultInventorySize:
            while True:
                try:
                    self.deleteItem(theGame().select(self._inventory, True))
                    break
                except:
                    print("Wrong value entered.")

    def use(self, elem):
        """Use a piece of equipment"""
        if elem is None:
            return
        self.checkEquipment(elem)
        if elem not in self._inventory:
            raise ValueError('Equipment ' + elem.name + 'not in inventory')
        if elem.use(self):
            self._inventory.remove(elem)

    def deleteItem(self, elem):
        """Delete an element from the inventory"""
        if len(self._inventory) > 0:
            if elem in self._inventory:
                self._inventory.remove(elem)
                theGame().addMessage("You have succesfully deleted the item : " + str(elem.name))
            else:
                theGame().addMessage("Could not find the item to delete. Maybe try with another value")

    def gainXP(self, creatureXP):

        self.xp += creatureXP

        theGame().addMessage("You gained {0} XP points".format(creatureXP))

        xpToUse = self.xp
        levelSteps = self.defaultLevelSize * self.level
        levelWon = 0

        if xpToUse > levelSteps:
            while xpToUse > levelSteps:
                xpToUse -= levelSteps

                self.gainLevel(1)

                levelSteps = self.defaultLevelSize * self.level
                levelWon += 1

            self.xp = xpToUse
            theGame().addMessage("You won {0} level(s) and are now level {1}".format(levelWon, self.level))

    def gainLevel(self, nbOfLevel):
        self.level += 1
        self.strength += nbOfLevel
        self.gold += nbOfLevel + self.level

        theGame().addMessage("You now have a strength of {0} and won {1} gold coins".format(self.strength, self.level))

    def verifyStomach(self):
        if self.stomach == 0:
            self.__dict__["hp"] -= 1

    def applyAllAmulets(self):
        return True


### EFFECTS
class Effect(object):

    def __init__(self, game, creature):
        self.game = game
        self.creature = creature
        self.name = ""
        self.value = 0
        self.info = ""

    def delete(self):
        self.game.activeEffects.remove(self)
        del self

    def update(self):
        self.action()

        if self.duration != None:
            self.duration -= 1

            if self.duration <= 0:
                self.desactivate()

    def action(self):
        self.game.addMessage(self.info)

    def activate(self):
        self.action()
        if self not in self.game.activeEffects:
            self.game.activeEffects.append(self)

    def desactivate(self):
        self.game.addMessage(self.info)
        self.delete()

    ### EPHEMERE EFFECTS


class EphemereEffect(Effect):

    def activate(self):
        super().activate()

        self.duration -= 1

        if self.duration <= 0:
            self.desactivate()


class HealEffect(EphemereEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "Recovering hp : +"

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature)
        self.name = "Heal"
        self.duration = duration
        self.level = level
        self.value = self.level * HealEffect.LEVEL_FACTOR

    def action(self):
        if self.creature._defaultHp > self.creature.hp + self.value:
            self.creature.hp += self.value
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {HealEffect.DESCRIPTION}{self.value}.\n"

        else:
            self.creature.hp = self.creature._defaultHp
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | Full Health : {self.creature.hp}/{self.creature.hp}.\n"

        super().action()

    def desactivate(self):
        self.info = f"[{self.creature.name}] heal effect disappeared"
        super().desactivate()


class PoisonEffect(EphemereEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "Losing hp : -"

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature)
        self.name = "Poison"
        self.duration = duration
        self.level = level
        self.value = self.level * PoisonEffect.LEVEL_FACTOR

    def action(self):
        self.creature.hp -= self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {PoisonEffect.DESCRIPTION}{self.value}"
        super().action()

    def desactivate(self):
        self.info = f"[{self.creature.name}] poison effect disappeared"
        super().desactivate()


class FeedEffect(EphemereEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "I'm eating : +"

    def __init__(self, game, creature, duration, level):
        super().__init__(game, creature)
        self.name = "Feed"
        self.duration = duration
        self.level = level
        self.value = self.level * FeedEffect.LEVEL_FACTOR

    def action(self):
        if self.creature._defaultStomachSize >= self.creature.stomach + self.value:
            self.creature.stomach += self.value
        else:
            self.creature.stomach = self.creature._defaultStomachSize

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {FeedEffect.DESCRIPTION}{self.value}"
        super().action()

    def desactivate(self):
        self.info = f"[{self.creature.name}] feed effect disappeared"
        super().desactivate()


class HungerEffect(EphemereEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "I'm hungry -"

    def __init__(self, game, creature, duration, level):
        super().__init__(self, game, creature)
        self.name = "Hunger"
        self.duration = duration
        self.level = level
        self.value = self.level * HungerEffect.LEVEL_FACTOR

    def activate(self):
        self.creature.stomach -= self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {HungerEffect.DESCRIPTION}{self.value}"
        super().activate()

    def desactivate(self):
        self.info = f"[{self.creature.name}] hunger effect disappeared"
        super().desactivate()


class TeleportEffect(EphemereEffect):  # IS AN INSTANT EFFECT

    DESCRIPTION = "You have been teleported"

    def action(self):
        """Teleport the creature"""
        r = self.game.floor.randRoom()
        c = r.randCoord()
        while not self.game.floor.get(c) == Map.ground:
            c = r.randCoord()
        self.game.floor.rm(self.game.floor.pos(self.creature))
        self.game.floor.put(c, self.creature)

        if isinstance(self.creature, Hero):
            self.info = TeleportEffect.DESCRIPTION
        else:
            self.info = f"The creature <{self.creature.name}> has been teleported"


### CONSTANT EFFECTS

class ConstantEffect(Effect):

    def __init__(self, game, creature):
        super().__init__(game, creature)
        self.hasBeenActivated = False

    def activate(self, game, creature):
        if not self.hasBeenActivated:
            super().activate()
            self.hasBeenActivated = True


class StrengthEffect(ConstantEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION_ACTIVATE = "I feel stronger : +"
    DESCRIPTION_DESACTIVATE = "- End of boost - I feel weaker... : -"

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
        super().activate(self.game, self.creature)

    def desactivate(self):
        self.creature.strength -= self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {HungerEffect.DESCRIPTION_DESACTIVATE}{self.value}"
        super().desactivate()


class WeaknessEffect(ConstantEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION_ACTIVATE = "I feel weaker : +"
    DESCRIPTION_DESACTIVATE = "- End of malus - I feel stronger... : -"

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

    def desactivate(self):
        self.creature.strength += self.value

        if isinstance(self.creature, Hero):
            self.info = f"{self.name}<{self.level}> | {WeaknessEffect.DESCRIPTION_DESACTIVATE}{self.value}"

        super().desactivate()


### EQUIPMENT
class Equipment(Element):
    """A piece of equipment"""

    def __init__(self, name, abbrv="", usage=None, durability=None):
        Element.__init__(self, name, abbrv)
        self.usage = usage
        self.durability = durability

    def meet(self, hero):
        """Makes the hero meet an element. The hero takes the element."""
        hero.take(self)
        theGame().addMessage("You pick up a " + self.name)
        return True

    def use(self, creature):
        """Uses the piece of equipment. Has effect on the hero according usage.
            Return True if the object is consumed."""
        if self.usage is None:
            theGame().addMessage("The " + self.name + " is not usable")
            return False

        elif isinstance(self, Weapon) and self.weaponType != Weapon._weaponTypeList[
            0]:  # The weapon is not an hitting weapon
            theGame().addMessage("The " + creature.name + " uses the " + self.name)

            # if self.durability != None:
            #     self.durability -= 1
            return self.usage(self, creature)

        else:
            theGame().addMessage("The " + creature.name + " uses the " + self.name)
            return self.usage(self, creature)

    # def isDurabilityValid(self):
    #     if self.durability == 0:
    #         return False
    #     return True


class Weapon(Equipment):
    """A weapon which can be used by the Hero or the monsters"""

    _weaponTypeList = ["hit", "throw", "projectile"]

    def __init__(self, name, abbrv="", weaponType=_weaponTypeList[0], usage=None, effectsList=None, damage=1,
                 durability=10):
        Equipment.__init__(self, name, abbrv, usage, durability)
        self.weaponType = weaponType

        if effectsList != None:
            self.effectsList = effectsList  # effects applied to the creature being hit
        else:
            self.effectsList = []

        self.damage = damage

    def applyWeaponEffects(self, creature):
        for effect in self.effectsList:
            creature.addEffect(effect, True)

    def throw(self, distance):
        return

    def launchProjectile(distance, projectileToUse):
        return


class Projectile(object):
    "Class to define the behaviour of projectiles"


class Amulet(Equipment):

    def __init__(self, name, abbrv="", usage=None, durability=None):
        Equipment.__init__(self, name, abbrv, usage, durability)


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

    def randCoord(self):
        """A random coordinate inside the room"""
        return Coord(random.randint(self.c1.x, self.c2.x), random.randint(self.c1.y, self.c2.y))

    def randEmptyCoord(self, map):
        """A random coordinate inside the room which is free on the map."""
        c = self.randCoord()
        while map.get(c) != Map.ground or c == self.center():
            c = self.randCoord()
        return c

    def decorate(self, map):
        """Decorates the room by adding a random equipment and monster."""
        map.put(self.randEmptyCoord(map), theGame().randEquipment())
        map.put(self.randEmptyCoord(map), theGame().randMonster())


class Map(object):
    """A map of a game floor.
        Contains game elements."""

    ground = '.'  # A walkable ground cell
    dir = {'z': Coord(0, -1), \
           'x': Coord(0, 1), \
           'd': Coord(1, 0), \
           'q': Coord(-1, 0), \
           'a': Coord(-1, -1), \
           'e': Coord(1, -1), \
           'w': Coord(-1, 1), \
           'c': Coord(1, 1), \
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
        self.generateRooms(7)
        self.reachAllRooms()
        self.put(self._rooms[0].center(), hero)
        for r in self._rooms:
            r.decorate(self)

    def addRoom(self, room):
        """Adds a room in the map."""
        self._roomsToReach.append(room)
        for y in range(room.c1.y, room.c2.y + 1):
            for x in range(room.c1.x, room.c2.x + 1):
                self._mat[y][x] = Map.ground

    def findRoom(self, coord):
        """If the coord belongs to a room, returns the room elsewhere returns None"""
        for r in self._roomsToReach:
            if coord in r:
                return r
        return None

    def intersectNone(self, room):
        """Tests if the room shall intersect any room already in the map."""
        for r in self._roomsToReach:
            if room.intersect(r):
                return False
        return True

    def dig(self, coord):
        """Puts a ground cell at the given coord.
            If the coord corresponds to a room, considers the room reached."""
        self._mat[coord.y][coord.x] = Map.ground
        r = self.findRoom(coord)
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

    def reachAllRooms(self):
        """Makes all rooms reachable.
            Start from the first room, repeats @reach until all rooms are reached."""
        self._rooms.append(self._roomsToReach.pop(0))
        while len(self._roomsToReach) > 0:
            self.reach()

    def randRoom(self):
        """A random room to be put on the map."""
        c1 = Coord(random.randint(0, len(self) - 3), random.randint(0, len(self) - 3))
        c2 = Coord(min(c1.x + random.randint(3, 8), len(self) - 1), min(c1.y + random.randint(3, 8), len(self) - 1))
        return Room(c1, c2)

    def generateRooms(self, n):
        """Generates n random rooms and adds them if non-intersecting."""
        for i in range(n):
            r = self.randRoom()
            if self.intersectNone(r):
                self.addRoom(r)

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

    def checkCoord(self, c):
        """Check if the coordinates c is valid in the map."""
        if not isinstance(c, Coord):
            raise TypeError('Not a Coord')
        if not c in self:
            raise IndexError('Out of map coord')

    def checkElement(self, o):
        """Check if o is an Element."""
        if not isinstance(o, Element):
            raise TypeError('Not a Element')

    def put(self, c, o):
        """Puts an element o on the cell c"""
        self.checkCoord(c)
        self.checkElement(o)
        if self._mat[c.y][c.x] != Map.ground:
            raise ValueError('Incorrect cell')
        if o in self._elem:
            raise KeyError('Already placed')
        self._mat[c.y][c.x] = o
        self._elem[o] = c

    def get(self, c):
        """Returns the object present on the cell c"""
        self.checkCoord(c)
        return self._mat[c.y][c.x]

    def pos(self, o):
        """Returns the coordinates of an element in the map """
        self.checkElement(o)
        return self._elem[o]

    def rm(self, c):
        """Removes the element at the coordinates c"""
        self.checkCoord(c)
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

    def moveAllMonsters(self):
        """Moves all monsters in the map.
            If a monster is at distance lower than 6 from the hero, the monster advances."""
        h = self.pos(self.hero)
        for e in self._elem:
            c = self.pos(e)
            if isinstance(e, Creature) and e != self.hero and c.distance(h) < 6:
                d = c.direction(h)
                if self.get(c + d) in [Map.ground, self.hero]:
                    self.move(e, d)

    def applyPoisonToAllMonsters(self):

        for e in self._elem:
            if isinstance(e, Creature) and not isinstance(e, Hero):
                effectToAdd = Effect(name="Heal Every Monster Test", benefic=False, effectFunc=Effect.heal,
                                     effectType="ephemere", duration=3, value=1)
                e.addEffect(effectToAdd)
                # print(e.__dict__["_ephemereEffects"], e.__dict__["name"])
                # break
                #### TO REMOVE (THE BREAK)

    def applyEffectsToAllMonsters(self):

        coordToDel = []
        for e in self._elem:
            if isinstance(e, Creature) and not isinstance(e, Hero):
                e.applyAllEffects()

                if e.__dict__["hp"] <= 0:
                    coordToDel.append(self.pos(e))

        for coord in coordToDel:
            self.rm(coord)


class Game(object):
    """ Class representing game state """

    """ available equipments """
    equipments = {0: [Equipment("gold", "o"), \
                      Equipment("potion heal", "!", usage=lambda self, hero: hero.addEffect(
                          Effect(name="Heal 3hp once", benefic=True, effectFunc=Effect.heal, effectType="instant",
                                 value=3), unique=True)), \
                      Equipment("basic bread", "§", usage=lambda self, hero: hero.addEffect(
                          Effect(name="Max food", benefic=True, effectFunc=Effect.feed, effectType="instant",
                                 value=hero.defaultStomachSize), unique=True)), \
                      Equipment("hunger mushroom", "£", usage=lambda self, hero: hero.addEffect(
                          Effect(name="Hunger", benefic=False, effectFunc=Effect.hunger, effectType="ephemere",
                                 duration=3, value=1), unique=True)), \
                      Equipment("poisonous mushroom", "%", usage=lambda self, hero: hero.addEffect(
                          Effect(name="Poison", benefic=False, effectFunc=Effect.poison, effectType="ephemere",
                                 duration=3, value=1), unique=True)), \
                      ], \
                  1: [Equipment("potion teleport", "!", usage=lambda self, hero: hero.addEffect(
                      Effect(name="Teleportation", benefic=True, effectFunc=Effect.teleport, effectType="instant"),
                      unique=True)), \
                      ], \
                  2: [Equipment("milk", "m", usage=lambda self, hero: hero.removeAllEffects(unique=True)), \
                      ], \
                  3: [Equipment("portoloin", "w", usage=lambda self, hero: hero.addEffect(
                      Effect(name="Telportation", benefic=True, effectFunc=Effect.teleport, effectType="instant"),
                      unique=False)), \
                      ], \
                  }

    """ available weapons """
    weapons = {
        0: [Weapon("Basic Sword", "†", weaponType=Weapon._weaponTypeList[0], usage=None, damage=3, durability=10)], \
        1: [], \
        2: [], \
        }

    """ available monsters """
    monsters = {0: [Creature("Goblin", hp=4, strength=1, xp=4), \
                    Creature("Bat", hp=2, abbrv="W", strength=1, xp=2)], \
                1: [Creature("Ork", hp=6, strength=2, xp=10), \
                    Creature("Blob", hp=10, xp=8)], \
                5: [Creature("Dragon", hp=20, strength=3, xp=100)], \
                }

    """ available actions """
    _actions = {'z': lambda h: theGame().floor.move(h, Coord(0, -1)), \
                'q': lambda h: theGame().floor.move(h, Coord(-1, 0)), \
                'x': lambda h: theGame().floor.move(h, Coord(0, 1)), \
                'd': lambda h: theGame().floor.move(h, Coord(1, 0)), \
                'a': lambda h: theGame().floor.move(h, Coord(-1, -1)), \
                'e': lambda h: theGame().floor.move(h, Coord(1, -1)), \
                'w': lambda h: theGame().floor.move(h, Coord(-1, 1)), \
                'c': lambda h: theGame().floor.move(h, Coord(1, 1)), \
 \
                'i': lambda h: theGame().addMessage(h.fullDescription()), \
                'k': lambda h: h.__setattr__('hp', 0), \
                'u': lambda h: h.use(theGame().select(h._inventory)), \
                ' ': lambda h: None, \
                'h': lambda hero: theGame().addMessage("Actions disponibles : " + str(list(Game._actions.keys()))), \
                't': lambda hero: hero.deleteItem(
                    theGame().selectItemToDel(hero._inventory) if len(hero._inventory) > 0 else False), \
                'b': lambda hero: hero.equipWeapon(theGame().selectWeapon(hero._inventory)) if any(
                    isinstance(elem, Weapon) for elem in hero._inventory) else theGame().addMessage(
                    "You don't have any weapon in your inventory"), \
                'n': lambda hero: hero.removeCurrentWeapon(), \
 \
                }

    def __init__(self, level=1, _message=None, hero=None, floor=None, numberOfRound=0):

        self.level = level
        self.activeEffects = []

        if hero == None:
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

        self.numberOfRound = numberOfRound

    def buildFloor(self):
        """Creates a map for the current floor."""
        self.floor = Map(hero=self.hero)

    def addMessage(self, msg):
        """Adds a message in the message list."""
        self._message.append(msg)

    def readMessages(self):
        """Returns the message list and clears it."""
        s = ''
        for m in self._message:
            s += m
        self._message.clear()
        return s

    def randElement(self, collect):
        """Returns a clone of random element from a collection using exponential random law."""
        x = random.expovariate(1 / self.level)
        for k in collect.keys():
            if k <= x:
                l = collect[k]
        return copy.copy(random.choice(l))

    def randEquipment(self):
        """Returns a random equipment."""
        return self.randElement(Game.equipments)

    def randMonster(self):
        """Returns a random monster."""
        return self.randElement(Game.monsters)

    def select(self, l):

        print("Choose an item> " + str([str(l.index(e)) + ": " + e.name for e in l]))

        c = getch()

        if c.isdigit() and int(c) in range(len(l)):
            return l[int(c)]

    def selectItemToDel(self, l):

        print("Choose an item to delete> " + str([str(l.index(e)) + ": " + e.name for e in l]))

        c = getch()

        if c.isdigit() and int(c) in range(len(l)) and len(l) != 0:
            return l[int(c)]

    def selectWeapon(self, l):

        listWeapon = [e for e in l if isinstance(e, Weapon)]

        print("Choose a weapon> " + str([str(listWeapon.index(e)) + ": " + e.name for e in listWeapon]))

        c = getch()

        if c.isdigit() and int(c) in range(len(listWeapon)) and len(listWeapon) != 0:
            return listWeapon[int(c)]

    def play(self):

        """Main game loop"""

        self.buildFloor()
        # self.hero.weaponSlot.append(theGame().weapons[0][0]) #BASIC SWORD
        # self.hero.addEffect(Effect(name="STRENGHT BOOST", benefic=True, effectFunc=Effect.giveStrength, effectType="constant", value=10))
        # self.hero.addEffect(Effect(name="Poison", benefic=False, effectFunc=Effect.poison, effectType="ephemere", duration=10, value=1), unique=True)
        # self.hero.take(theGame().equipments[2][0]) #MILK
        # self.hero.take(theGame().equipments[0][1]) #HEAL POTION

        # PoisonEffect.activate(PoisonEffect(self, self.hero, 3, 1))
        StrengthEffect.activate(StrengthEffect(self, self.hero, 10, 5))
        # HealEffect.activate(HealEffect(self, self.hero, 5, 1))

        print("--- Welcome Hero! ---")

        while self.hero.hp > 0:

            print()
            print(self.floor)
            print(self.hero.description())
            print(self.readMessages())

            self.hero.checkInventorySize()

            print(self.readMessages())

            # self.floor.applyPoisonToAllMonsters()

            c = getch()
            if c in Game._actions:
                Game._actions[c](self.hero)

                if c in {"a", "z", "e", "q", "d", "w", "x", "c"}:

                    self.floor.moveAllMonsters()
                    self.numberOfRound += 1

                    if self.numberOfRound % 20 == 0 and self.hero.__dict__["stomach"] > 0:
                        self.hero.__dict__["stomach"] -= 1

                    self.hero.verifyStomach()

                    for effect in self.activeEffects:

                        condition1 = isinstance(effect, EphemereEffect)
                        condition2 = isinstance(effect, ConstantEffect) and not effect.hasBeenActivated

                        if condition1 or condition2:
                            effect.update()

        print("--- Game Over ---")


def theGame(game=Game()):
    return game


getch = _find_getch()
theGame().play()








