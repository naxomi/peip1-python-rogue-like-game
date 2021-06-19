import copy
import math
import random
import CasesGraphiques as CG
import pygame


random.seed(2)


def _find_getch():
    """Single char input, only works only on mac/linux/windows OS terminals"""
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


def opp(x):
    return -x + 1


def clearList(liste):
    for i in range(len(liste)):
        for j in range(len(liste)):
            liste[i][j] = None


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

    def emptyAround(self, map):
        # Renvoie True si les coordonnées autour correspondent avec la liste demandée
        res = True
        for y in range(-1, 2):
            for x in range(-1, 2):
                res = res and (map.get(self + Coord(x, y)) == Map.ground or map.get(self + Coord(x, y)) == map.hero)
        return res

    def getEmptyCoordAround(self, map):
        l = []
        o = map.get(self)
        for i in range(-1, 2):
            for j in range(-1, 2):
                way = Coord(i, j)
                if map.checkMove(o, way) == Map.ground:
                    l.append(self + way)
        return random.choice(l)

    def getTupple(self):
        return (self.x, self.y)


class Element(object):
    """Base class for game elements. Have a name.
        Abstract class."""

    def __init__(self, name: str, abbreviation: str = "") -> None:
        self.name = name
        if abbreviation == "":
            abbreviation = name[0]
        self.abbreviation = abbreviation

        self.graphicOutput = None

    def __repr__(self) -> str:
        return self.abbreviation

    def description(self) -> str:
        """Description of the element"""
        return f"<{self.name}>"

    def meet(self, hero: "Hero") -> None:
        """Makes the hero meet an element. Not implemented. """
        raise NotImplementedError('Abstract Element')


class RoomObject(Element):

    def __init__(self, name, abbreviation='', usage=None):
        Element.__init__(self, name, abbreviation)

        self.usage = usage

        self.graphicOutput = []
        # self.graphicOutput.append(CG.getRoomObjectImage(self.name+'-0'))

        for i in range(2):
            try:
                self.graphicOutput.append(CG.getRoomObjectImage(self.name + '-' + str(i)))
            except:
                print("Not image for:", self.name + '-' + str(i))
                pass

    def meet(self, hero):
        """The roomObject is encountered by hero.
            The hero uses the roomObject.
            Return True if used."""
        if not isinstance(hero, Hero):
            return False
        ret = False

        g = the_game()
        ret = self.usage()

        return ret

    @staticmethod
    def monterEtage():
        g = the_game()
        if g.actualFloor + 1 < len(g.floorList):
            g.floor.rm(g.floor.pos(g.hero))

            g.actualFloor += 1
            g.floor = g.gv.floor = g.floorList[g.actualFloor]
            g.add_message('You are now in stage ' + str(g.actualFloor + 1) + '/' + str(len(g.floorList)))

            stairCoord = g.floor.pos(g._roomObjects['downstair'])
            newCoord = stairCoord.getEmptyCoordAround(g.floor)

            g.floor.put(newCoord, g.hero)
            g.hero.x = newCoord.x
            g.hero.y = newCoord.y
            return True
        return False

    @staticmethod
    def descendreEtage():
        g = the_game()
        if g.actualFloor - 1 >= 0:
            g.floor.rm(g.floor.pos(g.hero))

            g.actualFloor -= 1
            g.floor = g.gv.floor = g.floorList[g.actualFloor]
            g.add_message('You are now in stage ' + str(g.actualFloor + 1) + '/' + str(len(g.floorList)))

            stairCoord = g.floor.pos(g._roomObjects['upstair'])
            newCoord = stairCoord.getEmptyCoordAround(g.floor)

            g.floor.put(newCoord, g.hero)
            g.hero.x = newCoord.x
            g.hero.y = newCoord.y
            return True
        return False

    @staticmethod
    def meetMarchand():
        l = []
        for i in range(2):
            l.append(the_game().rand_element(Game.equipments))
        l.append(the_game().rand_element(Game._weapons))

        the_game().gv.drawMarchand(l)


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

        # Graphics
        self.graphicOutput = CG.getMonsterImage(self.name)

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

    defaultInventorySize = 10
    defaultStomachSize = 5
    defaultLevelSize = 25

    defaultHp = 10

    def __init__(self, name="Hero", hp=10, abbreviation="@", strength=2, level=1, xp=0, gold=0, stomach=10,
                 weapon_slot=None):
        Creature.__init__(self, name, hp, abbreviation, strength, xp, weapon_slot)

        self.xp = xp
        self.toNextLevel = Hero.defaultLevelSize

        self.level = level
        self.gold = gold
        self.stomach = stomach
        self.default_stomach_size = stomach

        # GRAPHICS
        images = CG.getHeroImage("Template")

        self.graphicOutput = images[0]
        self.animationUDLR = {(0, -1): images[12:16],  # cannot put Coord since it's not hashable

                              (0, 1): images[:4],
                              (-1, 1): images[:4],
                              (1, 1): images[:4],

                              (-1, 0): images[4:8],
                              (-1, -1): images[4:8],

                              (1, 0): images[8:12],
                              (1, -1): images[8:12],

                              }

        self.state = 0
        self.moovingUDLR = [False, False, False, False]

        self.x = 0
        self.y = 0

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

    def checkInvSize(self):
        if len(self._inventory) > Hero.defaultInventorySize:
            the_game().add_message("Inventaire complet.\nVeuillez supprimer un élément.")
            return False
        return True

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

    def buy(self, o):
        if isinstance(o, Equipment):
            if self.checkInvSize():
                if self.gold >= o.price:
                    self.gold -= o.price
                    self.take(o)
                    the_game().add_message(f'You bought {o.name} for {o.price} gold')
                else:
                    the_game().add_message(f'Not enough gold. {o.price - self.gold} gold left.')

    @staticmethod
    def choose_direction():
        print("Choose a direction to orientate yourself using the keys to move")

        choice = None
        while choice is None:
            for event in pygame.event.get():

                if event.type == pygame.KEYDOWN:
                    if the_game().gv.qwerty:
                        if event.key == pygame.K_w:
                            choice = "z"
                        elif event.key == pygame.K_a:
                            choice = "q"
                        elif event.key == pygame.K_s or event.key == pygame.K_x:
                            choice = "x"
                        elif event.key == pygame.K_d:
                            choice = "d"
                        elif event.key == pygame.K_q:
                            choice = "a"
                        elif event.key == pygame.K_e:
                            choice = "e"
                        elif event.key == pygame.K_z:
                            choice = "w"
                        elif event.key == pygame.K_c:
                            choice = "c"
                    else:
                        if event.key == pygame.K_z:
                            choice = "z"
                        elif event.key == pygame.K_q:
                            choice = "q"
                        elif event.key == pygame.K_s or event.key == pygame.K_x:
                            choice = "x"
                        elif event.key == pygame.K_d:
                            choice = "d"
                        elif event.key == pygame.K_a:
                            choice = "a"
                        elif event.key == pygame.K_e:
                            choice = "e"
                        elif event.key == pygame.K_w:
                            choice = "w"
                        elif event.key == pygame.K_c:
                            choice = "c"

                    if choice is not None:
                        the_game().gv.inventoryOn = False
                        return Map.dir[choice]

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
                    self.delete_item(item, True)
                break
            elif things_on_next_cell != the_game().floor.ground:
                if i == 0:
                    the_game().add_message("You can't throw the item in this direction")
                break
            elif things_on_next_cell == the_game().floor.ground:
                if i == 0:
                    the_game().floor.put(item_coord, item)
                elif i == distance - 1:
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
            self.creature.stomach = self.creature.stomach
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

    def __init__(self, name, abbreviation="", usage=None, durability=None, price=1):
        Element.__init__(self, name, abbreviation)
        self.usage = usage
        self.durability = durability
        self.price = price

        # GRAPHICS
        image = CG.getItemImage(self.name)
        self.graphicOutput = [pygame.transform.scale(image, (16, 16)), pygame.transform.scale(image, (32, 32))]

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

    def __init__(self, c1, c2, specialObjects=None):
        self.c1 = c1
        self.c2 = c2
        if specialObjects is None:
            specialObjects = []
        self.specialObjects = specialObjects

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

    def randEmptyMiddleCoord(self, map):
        # Same as rand_empty_coord but surrounded by ground
        e = Map.empty
        g = Map.ground
        m = ''
        l = []
        for y in range(self.c1.y + 1, self.c2.y):
            for x in range(self.c1.x + 1, self.c2.x):
                c = Coord(x, y)
                if c.emptyAround(map) and c != self.center():
                    l.append(c)
        if len(l) == 0:
            return None
        else:
            return random.choice(l)

    def decorate(self, map):
        """Decorates the room by adding a random equipment and monster."""
        for elem in self.specialObjects:
            map.put(self.randEmptyMiddleCoord(map), elem)
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

    empty = e = '_'  # A non walkable cell
    sizeFactor = round(16 * 1.25)

    def __init__(self, size=20, hero=None, putHero=True, floorNumber=None, specialRoom=None):
        self._mat = []
        self._elem = {}
        self._rooms = []
        self._roomsToReach = []
        self.floorNumber = floorNumber
        self.specialRoom = specialRoom

        for i in range(size):
            self._mat.append([Map.empty] * size)
        if hero is None:
            hero = Hero()
        self.hero = hero
        self.generate_rooms(7)
        self.reach_all_rooms()

        # Graphics

        self.graphicMap = []
        CG.generateGraphicMap(self)
        self.graphicElements = []
        for i in range(len(self.graphicMap)):
            l = []
            for j in range(len(self.graphicMap)):
                l.append(None)
            self.graphicElements.append(l)

        self.putRoomObjects()
        if putHero:
            self.put(self._rooms[0].center(), hero)
            self.hero.x = self._rooms[0].center().x
            self.hero.y = self._rooms[0].center().y
        for r in self._rooms:
            r.decorate(self)

        self.updateElements(0)

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

    def putRoomObjects(self):
        for key in Game._roomObjects:
            if key == "downstair" and self.floorNumber > 0:
                r = random.choice(self._rooms)
                r.specialObjects.append(Game._roomObjects[key])
            if key == "upstair" and self.floorNumber + 1 < the_game().nbFloors:
                r = random.choice(self._rooms)
                r.specialObjects.append(Game._roomObjects[key])

    def rand_room(self):
        """A random room to be put on the map."""
        c1 = Coord(random.randint(0, len(self) - 3), random.randint(0, len(self) - 3))
        c2 = Coord(min(c1.x + random.randint(3, 8), len(self) - 1), min(c1.y + random.randint(3, 8), len(self) - 1))
        return Room(c1, c2)

    def generate_rooms(self, n):
        """Generates n random rooms and adds them if non-intersecting."""
        if self.specialRoom is not None:
            self.add_room(Game._specialRoomsList[self.specialRoom])
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

    def inGraphicMap(self, c):
        return 0 <= c.x < len(self.graphicMap) and 0 <= c.y < len(self.graphicMap)

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
        try:
            self.check_coord(c)
        except IndexError:
            return Map.empty
        return self._mat[c.y][c.x]

    def get_without_coord(self, x, y):
        self.check_coord(Coord(x, y))
        return self._mat[y][x]

    def pos(self, o):
        """Returns the coordinates of an element in the map """
        if o in self._elem:
            self.check_element(o)
            return self._elem[o]
        else:
            return None

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
                if isinstance(e, Hero):
                    self.hero.x, self.hero.y = dest.x, dest.y
            elif isinstance(self.get(dest), RoomObject) and self.get(dest).meet(e):
                pass
            elif self.get(dest) != Map.empty and self.get(dest).meet(e) and self.get(dest) != self.hero:
                self.rm(dest)

    def checkMove(self, e, way):
        """Returns element in way"""
        orig = self.pos(e)
        dest = orig + way
        if dest in self:
            return self.get(dest)
        return self.empty

    def direction(self, c1, c2):
        """Returns the direction between two coordinates."""
        wayFinale = Coord(0, 0)
        for i in range(-1, 2):
            for j in range(-1, 2):
                way = Coord(i, j)
                inMap = 0 <= c1.x + way.x < len(self._mat) and 0 <= c1.y + way.y < len(self._mat)
                if inMap and (c1 + way).distance(c2) < (c1 + wayFinale).distance(c2) and (self.get(
                        c1 + way) == self.ground or self.get(c1 + way) == self.hero):
                    wayFinale = way
        return wayFinale

    def move_all_monsters(self):
        """Moves all monsters in the map.
            If a monster is at distance lower than 6 from the hero, the monster advances."""

        h = self.pos(self.hero)
        for e in self._elem:
            c = self.pos(e)
            if isinstance(e, Creature) and e != self.hero and c.distance(h) < 6:
                d = self.direction(c, h)
                if self.get(c + d) in [Map.ground, self.hero]:
                    self.move(e, d)

    def updateElements(self, state):
        clearList(self.graphicElements)
        for y in range(len(self._mat)):
            for x in range(len(self._mat)):

                elem = self.get(Coord(x, y))
                if elem != self.ground and elem != self.empty:
                    if isinstance(elem, Hero):
                        elem.x = x
                        elem.y = y
                    elif isinstance(elem, Creature):
                        self.graphicElements[y][x] = elem.graphicOutput[state]
                    elif isinstance(elem, Equipment):
                        self.graphicElements[y][x] = elem.graphicOutput[0]
                    elif isinstance(elem, RoomObject):
                        if len(elem.graphicOutput) == 2:
                            self.graphicElements[y][x] = elem.graphicOutput[state]
                        else:
                            self.graphicElements[y][x] = elem.graphicOutput[0]
        the_game().gv.updateBrouillard(self)


# TODO : Jaime wants to change something (qwerty / azerty)
class GraphicVariables(object):
    def __init__(self, hero):

        self.height = None
        self.width = None
        self.orig_x = None
        self.orig_y = None

        self.hero = hero
        self.floor = None
        self.screen = None

        # Frames
        self.running = True
        self.frameCount = 0
        self.monsterState = 0

        self.stop = False
        self.choice = 0
        self.choiceInv = 0
        self.newRound = False

        # Messages
        self.gameFont = None
        self.menuFont = None
        self._msg = []

        self.qwerty = False

        self.optionsMenuStart = [("Menu", False), ("", False), ("New Game", True), ("Show Controls", True),
                                 ("Choose Character", True), ("Exit Game", True)]
        self.optionsMenu = [("Menu", False), ("", False), ("Resume Game", True), ("Show Controls", True),
                            ("Choose Character", True), ("Exit Game", True)]
        self.optionsHero = [("Characters", False), ("", False), ("Template", True), ("Rogue", True), ("Engineer", True),
                            ("Warrior", True), ("Mage", True), ("Paladin", True)]
        self.optionsConstrols = [
            ("i : open inventory", False),
            ("k : suicide", False),
            ("t : delete item", False),
            ("b : select weapon", False),
            ("n : remove current weapon", False),
            ("", False),
            ("Return", True)]
        self.optionsGameOver = [("-- Game Over --", False), ("", False), ("Exit Game", True)]

        # Menu
        self.menuOn = True
        self.inventoryOn = False
        self.listeMenu = self.optionsMenuStart
        self.couleurMenu = (140, 140, 150)

        # Game Surfaces
        self.explosion = []
        for i in range(6):
            image = CG.getImage("Animations/explosion-" + str(i) + ".png")
            self.explosion.append(pygame.transform.scale(image, (40, 40)))

        self.hearts = []
        for i in range(5):
            image1 = CG.getImage("GUI/heart" + str(i) + "-0.png")
            image2 = CG.getImage("GUI/heart" + str(i) + "-1.png")
            self.hearts.append([image1, image2])

        self.blackhearts = []
        for i in range(5):
            image1 = CG.getImage("GUI/blackheart" + str(i) + "-0.png")
            image2 = CG.getImage("GUI/blackheart" + str(i) + "-1.png")
            self.blackhearts.append([image1, image2])

        self.xpbar = []
        for i in range(5):
            self.xpbar.append(CG.getImage("GUI/xp" + str(i) + ".png"))

        self.xpbord = []
        for i in range(3):
            self.xpbord.append(CG.getImage("GUI/bordexp" + str(i) + ".png"))

        self.blockSpace = pygame.transform.scale(CG.getImage("GUI/blockSpace.png"), (32, 32))
        self.brouillard = CG.getImage("Background/Brouillard.png")

        self.food = [CG.getImage("GUI/food0.png"), CG.getImage("GUI/food1.png")]
        self.dollar = CG.getImage("GUI/dollar.png")
        self.arrow = CG.getImage("GUI/arrow.png")

        # Music effects
        self._songs = ['song-1.mp3', 'song-2.mp3', 'song-3.mp3']

    def drawGUI(self, state):
        self.screen.fill((72, 62, 87), (self.width / 2, 0, self.width / 2, self.height))

        # Draw Character
        scale = round(self.height / 5)
        heroimage = pygame.transform.scale(self.hero.graphicOutput, (scale, scale))
        self.screen.blit(heroimage, ((self.width / 2) * (1 + 1 / 10), self.height / 10))

        # Draw hearts
        for i in range(Hero.defaultHp):
            # self.screen.blit(self.blockSpace[0], (self.width/2*(1+1/5)+18*i,self.height/5))
            if self.hero.hp - i > 0:
                image = self.hearts[0][state]
            elif self.hero.hp - i == -0.25:
                image = self.hearts[1][state]
            elif self.hero.hp - i == -0.5:
                image = self.hearts[2][state]
            elif self.hero.hp - i == -0.75:
                image = self.hearts[3][state]
            else:
                image = self.hearts[4][state]

            self.screen.blit(image, (self.width / 2 * (1 + 3 / 10) + 18 * i, self.height * 3 / 20))

        # Draw food
        for i in range(Hero.defaultStomachSize):
            if self.hero.stomach - i > 0:
                self.screen.blit(self.food[0], (self.width / 2 * (1 + 3 / 10) + 18 * i, self.height * 3 / 20 + 25))
            else:
                self.screen.blit(self.food[1], (self.width / 2 * (1 + 3 / 10) + 18 * i, self.height * 3 / 20 + 25))

        # Draw xp
        a = 0
        tnl = self.hero.toNextLevel
        exp = self.hero.xp * 100 / tnl

        for i in range(1, 11):
            if exp >= 10:
                image = self.xpbar[0]
                exp -= 10
            elif exp >= 7.5:
                image = self.xpbar[1]
                exp -= 7.5
            elif exp >= 5:
                image = self.xpbar[2]
                exp -= 5
            elif exp >= 2.5:
                image = self.xpbar[3]
                exp -= 2.5
            else:
                image = self.xpbar[4]

            self.screen.blit(image, (self.width / 2 * (1 + 3 / 10) + 18 * (i - 1), self.height * 3 / 20 + 50))

            if i == 1:
                self.screen.blit(self.xpbord[0],
                                 (self.width / 2 * (1 + 3 / 10) + 18 * (i - 1), self.height * 3 / 20 + 50))
            elif i == 10:
                self.screen.blit(self.xpbord[2],
                                 (self.width / 2 * (1 + 3 / 10) + 18 * (i - 1), self.height * 3 / 20 + 50))
            else:
                self.screen.blit(self.xpbord[1],
                                 (self.width / 2 * (1 + 3 / 10) + 18 * (i - 1), self.height * 3 / 20 + 50))

        # Draw Hero Level
        text = self.gameFont.render('Level: ' + str(self.hero.level), True, (0, 0, 0))
        self.screen.blit(text, (self.width / 2 * (1 + 3 / 10), self.height * 3 / 20 - 30))

        # Draw gold
        self.screen.blit(self.dollar, (self.width / 2 * (1 + 3 / 10), self.height * 3 / 20 + 75))
        text = self.gameFont.render(str(self.hero.gold), True, (0, 0, 0))
        self.screen.blit(text, (self.width / 2 * (1 + 3 / 10) + 30, self.height * 3 / 20 + 76))

        # Inventaire
        sf = 2
        case = 16

        self.screen.blit(self.blockSpace, (self.width / 2 * (1 + 1 / 10) + 65, self.height * 7 / 20))
        if len(self.hero.weapon_slot) != 0:
            self.screen.blit(self.hero.weapon_slot[0].graphicOutput[1],
                             (self.width / 2 * (1 + 3 / 20), self.height * 7 / 20))

        for i in range(Hero.defaultInventorySize):
            self.screen.blit(self.blockSpace, (self.width / 2 * (1 + 3 / 10) + case * i * sf, self.height * 7 / 20))
            if i < len(self.hero._inventory):
                if sf != 1:
                    image = pygame.transform.scale(self.hero._inventory[i].graphicOutput[1], (16 * sf, 16 * sf))
                else:
                    image = self.hero._inventory[i].graphicOutput[1]
                self.screen.blit(image, (self.width / 2 * (1 + 3 / 10) + case * i * sf, self.height * 7 / 20))

        # Fleche Inventaire
        if self.inventoryOn:
            if len(self.hero._inventory) != 0:
                self.choiceInv = self.choiceInv % len(self.hero._inventory)
            else:
                self.choiceInv = 0
            if sf != 2:
                image = pygame.transform.scale(self.arrow, (16 * sf, 16 * sf))
            else:
                image = self.arrow
            self.screen.blit(image, (
                self.width / 2 * (1 + 3 / 10) + 7 + case * self.choiceInv * sf, self.height * 7 / 20 - 21))

    def drawMap(self):
        self.screen.fill((80, 74, 85), (0, 0, self.width / 2, self.height))
        for y in range(self.height // Map.sizeFactor):
            for x in range(self.width // (2 * Map.sizeFactor)):
                self.screen.blit(self.brouillard, (x * Map.sizeFactor, y * Map.sizeFactor))

        for y in range(len(self.floor.graphicMap)):
            for x in range(len(self.floor.graphicMap[y])):
                pos = (Map.sizeFactor * x + self.orig_x, Map.sizeFactor * y + self.orig_y)
                if self.floor.graphicMap[y][x][1]:
                    self.screen.blit(self.floor.graphicMap[y][x][0], pos)
                else:
                    self.screen.blit(self.brouillard, pos)

    def drawElements(self, monsterState):
        self.floor.updateElements(monsterState)
        for y in range(len(self.floor.graphicElements)):
            for x in range(len(self.floor.graphicElements)):
                case = self.floor.graphicElements[y][x]
                if case != None and self.floor.graphicMap[y][x][1]:
                    if isinstance(self.floor._mat[y][x], RoomObject):
                        if self.floor._mat[y][x].name == "upstair":
                            relief = 20
                        else:
                            relief = 0
                    else:
                        relief = Map.sizeFactor / 4
                    self.screen.blit(case,
                                     (Map.sizeFactor * x + self.orig_x, Map.sizeFactor * y + self.orig_y - relief))

    # TODO : Create a function to manage messages that are too long
    def drawMessage(self, time):
        # Draw Message self.screen
        self.screen.fill((20, 12, 28), (
            (self.width / 2) * (1 + 1 / 8), self.height * 3 / 4, (self.width / 2) * 6 / 8, self.height / 5))
        b = 5
        self.screen.fill((140, 140, 150), (
            (self.width / 2) * (1 + 1 / 8) + b, self.height * 3 / 4 + b, (self.width / 2) * 6 / 8 - 2 * b,
            self.height / 5 - 2 * b))

        newmsg = the_game().read_messages()
        nblines = len(self._msg)
        msgNuls = []
        for k in newmsg:
            self._msg.append([k, time])
            if len(self._msg) > 5:
                self._msg.pop(0)
        for i in range(nblines):
            self.screen.blit(self._msg[i][0],
                             ((self.width / 2) * (1 + 1 / 8) + 15, self.height * 3 / 4 + 5 + 20 * i + 10))
            self._msg[i][1] -= 1
            if self._msg[i][1] <= 0:
                msgNuls.append(i)

        for j in msgNuls:
            if j < len(self._msg):
                self._msg.pop(j)

    def drawMenu(self, listeMenu, couleur=(140, 140, 150)):
        self.screen.fill((255, 255, 51), (self.width / 4, self.height / 4, self.width / 2, self.height / 2))
        b = 5
        self.screen.fill(couleur,
                         (self.width / 4 + b, self.height / 4 + b, self.width / 2 - 2 * b, self.height / 2 - 2 * b))

        self.choice = self.choice % len(listeMenu)
        size = 40

        for i in range(len(listeMenu)):
            if i == self.choice:
                if listeMenu[i][1]:
                    f = "> "
                else:
                    f = "  "
                    self.choice = (self.choice + 1) % len(listeMenu)
            else:
                f = "  "
            # while
            if isinstance(listeMenu[i][0], Equipment):
                objet = listeMenu[i][0].name + ' [ ' + str(listeMenu[i][0].price) + ' ]'
            else:
                objet = listeMenu[i][0]

            text = self.menuFont.render(f + objet, True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.width / 2, self.height / 4 + (i + 1) * size))
            self.screen.blit(text, text_rect)

    def drawMarchand(self, listeObjets):
        lm = [('Que voulez vous acheter ?', False), ('', False)]

        for o in listeObjets:
            lm.append((o, True))
        lm += [('', False), ('Maybe Later', True)]

        self.listeMenu = lm
        self.couleurMenu = (30, 212, 157)
        self.menuOn = True

    def drawHeroMove(self):
        h = self.hero
        sf = Map.sizeFactor
        persp = -sf / 4

        hasMoved = False

        way = Coord(0, 0)
        if h.moovingUDLR[0]:
            # UP
            way += Coord(0, -1)
        if h.moovingUDLR[1]:
            # DOWN
            way += Coord(0, 1)
        if h.moovingUDLR[2]:
            # LEFT
            way += Coord(-1, 0)
        if h.moovingUDLR[3]:
            # RIGHT
            way += Coord(1, 0)

        if way != Coord(0, 0):

            elemInWay = self.floor.checkMove(h, way)
            if elemInWay == self.floor.ground:
                pos = (sf * h.x + way.x * h.state * sf / 4 + self.orig_x,
                       sf * h.y + way.y * h.state * sf / 4 + self.orig_y + persp)

                self.screen.blit(h.animationUDLR[way.getTupple()][h.state], pos)
                h.state += 1
                hasMoved = True

                if h.state >= 4:
                    h.state = 0
                    self.floor.move(h, way)
                    self.newRound = True

                    if self.stop:
                        h.moovingUDLR = [False] * 4
                        self.stop = False

            elif isinstance(elemInWay, Creature):
                self.floor.move(h, way)
                self.newRound = True
                # pos = Coord(h.x+way.x,h.y+way.y)
                for i in range(6):
                    self.screen.blit(self.explosion[i], (
                        sf * (h.x + way.x) + self.orig_x - 12, sf * (h.y + way.y) + self.orig_y + persp - 12))
                    self.screen.blit(h.graphicOutput, (sf * h.x + self.orig_x, sf * h.y + self.orig_y + persp))
                    pygame.display.update()
                    pygame.time.delay(50)

            elif isinstance(elemInWay, Element):
                self.floor.move(h, way)

        if not hasMoved:
            self.screen.blit(h.graphicOutput, (sf * h.x + self.orig_x, sf * h.y + self.orig_y + persp))

    def playerPlays(self, event):
        do = False
        if event.type == pygame.KEYDOWN:
            keydownBool = True
            do = True
        elif event.type == pygame.KEYUP:
            keydownBool = False
            do = True

        # Mouvement
        if do:

            if keydownBool or self.hero.state == 0:

                if self.qwerty:

                    if event.key == pygame.K_w:
                        self.hero.moovingUDLR[0] = keydownBool
                    elif event.key == pygame.K_s:
                        self.hero.moovingUDLR[1] = keydownBool
                    elif event.key == pygame.K_a:
                        self.hero.moovingUDLR[2] = keydownBool
                    elif event.key == pygame.K_d:
                        self.hero.moovingUDLR[3] = keydownBool
                else:
                    if event.key == pygame.K_z:
                        self.hero.moovingUDLR[0] = keydownBool
                    elif event.key == pygame.K_s:
                        self.hero.moovingUDLR[1] = keydownBool
                    elif event.key == pygame.K_q:
                        self.hero.moovingUDLR[2] = keydownBool
                    elif event.key == pygame.K_d:
                        self.hero.moovingUDLR[3] = keydownBool

                # Actions
                if keydownBool:
                    self.chooseAction(event)

            else:
                self.stop = True

    def chooseAction(self, event):
        if event.key == pygame.K_k:
            Game._actions['k'](self.hero)
        elif event.key == pygame.K_i:
            self.inventoryOn = not self.inventoryOn
        elif event.key == pygame.K_b:
            Game._actions['b'](self.hero)
        elif event.key == pygame.K_n:
            Game._actions['n'](self.hero)

    def chooseInMenu(self, event):
        if self.qwerty:
            if event.key == pygame.K_w:
                self.choice -= 1
            elif event.key == pygame.K_s:
                self.choice += 1
        else:
            if event.key == pygame.K_z:
                self.choice -= 1
            elif event.key == pygame.K_s:
                self.choice += 1

        if event.key == pygame.K_RETURN:

            thischoice = self.listeMenu[self.choice][0]

            if thischoice == "New Game":
                self.menuOn = not self.menuOn
                self.listeMenu = self.optionsMenu

            elif thischoice == "Resume Game" or thischoice == 'Maybe Later':
                self.menuOn = not self.menuOn

            elif thischoice == "Exit Game":
                self.running = False

            elif thischoice == "Choose Character":
                self.listeMenu = self.optionsHero
                self.choice = 0

            elif self.listeMenu[self.choice] in self.optionsHero:
                self.changeHeroAppearance(thischoice)
                self.choice = 0
                self.listeMenu = self.optionsMenu

            elif thischoice == "Show Controls":
                self.listeMenu = self.optionsConstrols

            elif thischoice == "Return":
                self.listeMenu = self.optionsMenu

            # Marchand

            elif isinstance(thischoice, Equipment):
                self.hero.buy(thischoice)
                self.menuOn = False

    def chooseInInventory(self, event):

        if self.qwerty:
            if event.key == pygame.K_a:
                self.choiceInv -= 1
            elif event.key == pygame.K_d:
                self.choiceInv += 1

        else:
            if event.key == pygame.K_q:
                self.choiceInv -= 1
            elif event.key == pygame.K_d:
                self.choiceInv += 1

        # Use equipment
        if event.key == pygame.K_RETURN or event.key == pygame.K_u:
            Game._actions['u'](self.hero)
            self.inventoryOn = False

        elif event.key == pygame.K_t:
            Game._actions["t"](self.hero)
            self.inventoryOn = False

        elif event.key == pygame.K_b:
            Game._actions["b"]
            self.inventoryOn = False

        elif event.key == pygame.K_n:
            Game._actions["n"]
            self.inventoryOn = False

        elif event.key == pygame.K_i:
            self.inventoryOn = True

        elif event.key == pygame.K_l:
            Game._actions['l'](self.hero)

        self.floor.updateElements(self.monsterState)

    def changeHeroAppearance(self, costume):
        images = CG.getHeroImage(costume)
        self.hero.graphicOutput = images[0]
        self.hero.animationUDLR = [images[12:16], images[:4], images[4:8], images[8:12]]

    def selectFromInventory(self, classe):
        if self.choiceInv < len(self.hero._inventory) and isinstance(self.hero._inventory[self.choiceInv], classe):
            return self.hero._inventory[self.choiceInv]
        return None

    def drawGameScreen(self):
        self.drawMap()
        self.drawElements(self.monsterState)
        self.drawHeroMove()

    def updateBrouillard(self, map):
        for o in [map.hero, Game.monsters[20][0]]:
            if isinstance(o, Hero):
                x = self.hero.x
                y = self.hero.y
            else:
                c = map.pos(o)
                if c is None:
                    break
                x = c.x
                y = c.y

            rayon = 5

            for i in range(-rayon, rayon + 1):
                for j in range(-rayon, rayon + 1):
                    c = Coord(x + i, y + j)
                    if self.floor is not None and self.floor.inGraphicMap(c):
                        if Coord(x, y).distance(c) <= rayon:
                            self.floor.graphicMap[y + j][x + i][1] = True

    def play_next_song(self):
        cle = 'Images/musiques/'
        self._songs = self._songs[1:] + [self._songs[0]]  # move current song to the back of the list
        pygame.mixer.music.load(cle + self._songs[0])
        pygame.mixer.music.play()
        print(self._songs[0])


class Game(object):
    """ Class representing game state """

    """ available equipments """
    equipments = {0: [Equipment("gold", "o"),
                      Equipment("healing potion", "!",
                                usage=lambda self, hero: HealEffect.activate(HealEffect(the_game(), hero, 1, 3))),
                      Equipment("basic bread", "§", usage=lambda self, hero: FeedEffect.activate(
                          FeedEffect(the_game(), hero, 1, hero.default_stomach_size))),
                      Equipment("hunger mushroom", "£",
                                usage=lambda self, hero: HungerEffect.activate(HungerEffect(the_game(), hero, 3, 1))),
                      Equipment("poisonous mushroom", "%",
                                usage=lambda self, hero: PoisonEffect.activate(PoisonEffect(the_game(), hero, 3, 1))),
                      ],
                  1: [Equipment("teleport potion", "!",
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
    _weapons = {
        0: [Weapon("Basic Sword", "†", "hitting", usage=None, damage=3, durability=10)],
        1: [Weapon("Shuriken", "*", "hitting", usage=lambda self, hero: Weapon.hit)],
        2: [],
    }

    """ available monsters """
    monsters = {0: [Creature("Goblin", hp=4, strength=1, xp=4), \
                    Creature("Bat", hp=2, abbreviation="W", strength=1, xp=2), \
                    Creature("BabyDemon", hp=2, strength=2, xp=4)], \
                1: [Creature("Ork", hp=6, strength=2, xp=10), \
                    Creature("Blob", hp=10, xp=8), \
                    Creature("Angel", hp=10, strength=1, xp=4)], \
                3: [Creature("Poisonous spider", hp=5, xp=10, strength=0, abbreviation="&",
                             powers_list=[[PoisonEffect, 2, 1]])],
                5: [Creature("Dragon", hp=20, strength=3, xp=50)],
                20: [Creature("Death", hp=50, strength=3, xp=100, abbreviation='ñ')] \
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

                # 'i': lambda h: the_game().add_message(h.full_description()),
                'k': lambda h: h.__setattr__('hp', 0),
                # 'u': lambda h: h.use(the_game().select(h._inventory)),
                'u': lambda h: h.use(the_game().gv.selectFromInventory(Equipment)),
                ' ': lambda h: None,
                'h': lambda hero: the_game().add_message("Actions available : " + str(list(Game._actions.keys()))),
                't': lambda hero: hero.delete_item(
                    the_game().select_item_to_del(hero._inventory) if len(hero._inventory) > 0 else False),
                'b': lambda hero: hero.equip_weapon(the_game().select_weapon(hero._inventory)) if any(
                    isinstance(elem, Weapon) for elem in hero._inventory) else the_game().add_message(
                    "You don't have any weapon in your inventory"),
                'n': lambda hero: hero.remove_current_weapon(),
                'l': lambda hero: hero.throw_item(the_game().gv.selectFromInventory(Equipment), 5)

                }

    _roomObjects = {'upstair': RoomObject('upstair', "^", usage=lambda: RoomObject.monterEtage()),
                    'downstair': RoomObject('downstair', "v", usage=lambda: RoomObject.descendreEtage()),
                    'marchand': RoomObject('marchand', "€", usage=lambda: RoomObject.meetMarchand()),
                    }

    _specialRoomsList = {"finalBoss": Room(Coord(1, 1), Coord(19, 10), [monsters[20][0]]),
                         'marchand': Room(Coord(15, 15), Coord(19, 19), [_roomObjects['marchand']]),
                         }

    sizeFactor = Map.sizeFactor

    def __init__(self, level=1, hero=None, nbFloors=2):

        self.level = level
        self.active_effects = []
        self._message = []

        if hero is None:
            hero = Hero()
        self.hero = hero

        self.nbFloors = nbFloors
        self.floorList = []
        self.actualFloor = 0
        self.floor = None

        self.numberOfRound = 0
        self.applyEffectsBool = False

        # GRAPHICS
        self.gv = GraphicVariables(self.hero)

    def build_floor(self):
        """Creates a map for the current floor."""

        placeHero = True
        rand = random.randint(0, self.nbFloors - 2)
        marchand = None

        for i in range(self.nbFloors):
            print('Building Floor ' + str(i + 1) + '/' + str(self.nbFloors))

            if i == rand:
                self.floorList.append(Map(hero=self.hero, putHero=placeHero, floorNumber=i, specialRoom='marchand'))
            elif i == self.nbFloors - 1:
                self.floorList.append(Map(hero=self.hero, putHero=placeHero, floorNumber=i, specialRoom='finalBoss'))
            else:
                self.floorList.append(Map(hero=self.hero, putHero=placeHero, floorNumber=i))
            placeHero = False

        self.gv.floor = self.floor = self.floorList[self.actualFloor]

    def add_message(self, msg):
        """Adds a message in the message list."""
        if '\n' in msg:
            l = msg.split('\n')
            for m in l:
                self._message.append(m)

        else:
            self._message.append(msg)

    def read_messages(self):
        """Returns the message list and clears it."""
        renders = []
        for m in self._message:
            renders.append(self.gv.gameFont.render(m, True, (0, 0, 0)))

        self._message.clear()
        return renders.copy()

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
        elif len(l) == 0:
            print("You don't have any item in your inventory.")

    @staticmethod
    def select_item_to_del(items_list: list) -> Element:

        print("Choose an item to delete> " + str([str(items_list.index(e)) + ": " + e.name for e in items_list]))

        c = getch()

        if c.isdigit() and int(c) in range(len(items_list)) and len(items_list) != 0:
            return items_list[int(c)]
        elif len(l) == 0:
            print("You don't have any item in your inventory.")

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

    def playWithGraphics(self):

        print("\n--- Initialiting Graphics ---")
        print("Loading ...")

        self.build_floor()
        print(self.floor)

        pygame.init()

        # Create the screen
        infoObject = pygame.display.Info()
        height = self.gv.height = infoObject.current_h - 60
        width = self.gv.width = infoObject.current_w

        # orig_x = self.gv.orig_x = width/10
        orig_x = self.gv.orig_x = width / 4 - 10 * Map.sizeFactor
        orig_y = self.gv.orig_y = height / 6

        self.gv.screen = pygame.display.set_mode((width, height))

        # Title and Icon
        pygame.display.set_caption("Rogue: Jaime et Raphaël")
        icon = pygame.image.load("images/magicsword.png")
        pygame.display.set_icon(icon)

        # Font
        self.gv.gameFont = pygame.font.SysFont('Agencyfc', 30)
        self.gv.menuFont = pygame.font.SysFont('papyrus', 40)

        # Music
        SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(SONG_END)
        self.gv.play_next_song()

        # Initialize Brouillard
        self.gv.updateBrouillard(self.floor)

        while self.gv.running:

            # pygame.time.Clock().tick()
            pygame.time.delay(50)

            if self.gv.frameCount > 10:
                self.gv.monsterState = opp(self.gv.monsterState)
                self.gv.frameCount = 0
            self.gv.frameCount += 1

            # Events
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.gv.running = False

                elif event.type == SONG_END:
                    self.gv.play_next_song()

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        self.gv.menuOn = not self.gv.menuOn
                        self.gv.listeMenu = self.gv.optionsMenu
                        self.gv.couleurMenu = (140, 140, 150)

                        self.gv.inventoryOn = False

                    if self.gv.menuOn:
                        self.gv.chooseInMenu(event)

                    if self.gv.inventoryOn:
                        self.gv.chooseInInventory(event)

                if not self.gv.inventoryOn:
                    self.gv.playerPlays(event)

            # Menu
            if self.gv.menuOn:
                self.gv.drawMenu(self.gv.listeMenu, self.gv.couleurMenu)

            else:
                # Background
                self.gv.drawGUI(self.gv.monsterState)

                if self.hero.hp <= 0:
                    # self.hero.hp = 1
                    self.gv.listeMenu = self.gv.optionsGameOver
                    self.gv.menuOn = True

                self.hero.check_inventory_size()

                if self.gv.newRound:
                    self.gv.newRound = False
                    self.numberOfRound += 1
                    self.applyEffectsBool = True

                    # self.gv.updateBrouillard()
                    self.floor.move_all_monsters()

                    if self.numberOfRound % 20 == 0 and self.hero.__dict__["stomach"] > 0:
                        self.hero.__dict__["stomach"] -= 1
                    self.hero.verify_stomach()

                if self.applyEffectsBool:
                    if len(self.active_effects) != 0:
                        i = 0
                        while i < len(self.active_effects):
                            if not self.active_effects[i].update():
                                i += 1
                    self.applyEffectsBool = False

                # Messages
                self.gv.drawMessage(200)

                self.gv.drawGameScreen()

            pygame.display.update()
        # running = False

        pygame.quit()


def the_game(game=Game()):
    return game


# getch = _find_getch()
# the_game().play()
the_game().playWithGraphics()
