import copy
import math
import random
import CasesGraphiques as CG
import pygame


# random.seed(234789)

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


def opp(x: int) -> int:
    return -x + 1


def clear_list(list_to_clear: list) -> None:
    for i in range(len(list_to_clear)):
        for j in range(len(list_to_clear)):
            list_to_clear[i][j] = None


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

    def empty_around(self, actual_map: "Map") -> bool:
        # Return True if the coordinates around are corresponding
        res = True
        for y in range(-1, 2):
            for x in range(-1, 2):
                res = res and (actual_map.get(self + Coord(x, y)) == Map.ground or actual_map.get(
                    self + Coord(x, y)) == actual_map.hero)
        return res

    def get_empty_coord_around(self, actual_map: "Map") -> "Coord":
        available_coord_list = []
        o = actual_map.get(self)
        for i in range(-1, 2):
            for j in range(-1, 2):
                way = Coord(i, j)
                if actual_map.check_move(o, way) == Map.ground:
                    available_coord_list.append(self + way)
        return random.choice(available_coord_list)

    def get_tuple(self) -> tuple:
        return self.x, self.y


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

    def __init__(self, name: str = "", abbreviation: str = "", usage: "function" = None) -> None:
        Element.__init__(self, name, abbreviation)

        self.usage = usage

        self.graphicOutput = []

        for i in range(2):
            try:
                self.graphicOutput.append(CG.get_room_object_image(self.name + '-' + str(i)))
            except FileNotFoundError:
                print("Not image for:", self.name + '-' + str(i))
                pass

    def meet(self, hero: "Hero") -> bool:
        """The roomObject is encountered by hero.
            The hero uses the roomObject.
            Return True if used."""
        if not isinstance(hero, Hero):
            return False
        return self.usage()

    @staticmethod
    def go_upstair() -> bool:
        g = the_game()
        if g.actual_floor + 1 < len(g.floor_list):
            g.floor.rm(g.floor.pos(g.hero))

            g.actual_floor += 1
            g.floor = g.gv.floor = g.floor_list[g.actual_floor]
            g.add_message('You are now in stage ' + str(g.actual_floor + 1) + '/' + str(len(g.floor_list)))

            stair_coord = g.floor.pos(g._room_objects['downstair'])
            new_coord = stair_coord.get_empty_coord_around(g.floor)

            g.floor.put(new_coord, g.hero)
            g.hero.x = new_coord.x
            g.hero.y = new_coord.y
            return True
        return False

    @staticmethod
    def go_downstair() -> bool:
        g = the_game()
        if g.actual_floor - 1 >= 0:
            g.floor.rm(g.floor.pos(g.hero))

            g.actual_floor -= 1
            g.floor = g.gv.floor = g.floor_list[g.actual_floor]
            g.add_message('You are now in stage ' + str(g.actual_floor + 1) + '/' + str(len(g.floor_list)))

            stair_coord = g.floor.pos(g._room_objects['upstair'])
            new_coord = stair_coord.get_empty_coord_around(g.floor)

            g.floor.put(new_coord, g.hero)
            g.hero.x = new_coord.x
            g.hero.y = new_coord.y
            return True
        return False

    @staticmethod
    def meet_trader() -> None:
        list_of_items_sold = []
        for i in range(2):
            list_of_items_sold.append(
                the_game().rand_element(Game.equipments, the_game().floor_list[the_game().actual_floor].floor_number))
        list_of_items_sold.append(
            the_game().rand_element(Game.weapons, the_game().floor_list[the_game().actual_floor].floor_number))

        the_game().gv.draw_trader(list_of_items_sold)


class Creature(Element):
    """A creature that occupies the dungeon.
        Is an Element. Has hit points and strength."""

    default_inventory_size = 10

    def __init__(self, name: str, hp: int, abbreviation: str = "", strength: int = 1, xp: int = 0,
                 weapon_slot: list = None, powers_list: list = None, cooldown: int = 0) -> None:
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

        self.cooldown = 0
        self._default_cooldown = cooldown

        self._inventory = []

        # Graphics
        self.graphicOutput = CG.get_monster_image(self.name)

    def description(self) -> str:
        """Description of the creature"""
        if self.hp > 0:
            return Element.description(self) + "(" + str(self.hp) + ")"
        return Element.description(self) + "(0)"

    def gain_xp(self, xp_point):
        raise NotImplementedError

    def gain_level(self, nb_of_level):
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
                if other.cooldown == 0:  # The cooldown ended
                    effect_infos_list[0].add_effect(
                        effect_infos_list[0](self, effect_infos_list[1], effect_infos_list[2]))
                    other.cooldown = other._default_cooldown
                else:
                    other.cooldown -= 1

        if other.has_weapon():
            self.hp -= other.current_weapon().damage
        else:
            self.hp -= other.strength

    def equip_weapon(self, weapon: "Weapon") -> None:
        if len(self.weapon_slot) != 0:
            self._inventory.append(self.weapon_slot[0])
            self.weapon_slot.clear()

        self.weapon_slot.append(weapon)
        self._inventory.remove(weapon)
        the_game().add_message(f"You equipped {weapon.name}")

    def remove_current_weapon(self) -> None:
        if self.current_weapon():
            if len(self._inventory) < self.default_inventory_size:
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


class Hero(Creature):
    """The hero of the game.
        Is a creature. Has an inventory of elements. """

    default_inventory_size = 10
    default_stomach_size = 10
    default_level_size = 25

    default_hp = 10

    def __init__(self, name="Hero", hp=default_hp, abbreviation="@", strength=2, level=1, xp=24, gold=0,
                 stomach=default_stomach_size,
                 weapon_slot=None):
        Creature.__init__(self, name, hp, abbreviation, strength, xp, weapon_slot)

        self.xp = xp
        self.level_step = Hero.default_level_size

        self.level = level
        self.gold = gold
        self.stomach = stomach
        self.default_stomach_size = stomach

        # GRAPHICS
        images = CG.get_hero_image("Template")

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
        self.moving_UDLR = [False, False, False, False]

        self.x = 0
        self.y = 0

    def description(self):
        """Description of the hero"""
        if len(self.weapon_slot) != 0:
            return Creature.description(self) + " |" + str(self.current_weapon()) + "|"
        else:
            return Creature.description(self)

    def full_description(self):
        """Complete description of the hero"""
        res = ''
        for e in self.__dict__:

            if e[0] != ' ' and "default" not in e:
                if e == "xp":
                    res += '> ' + e + ' : ' + str(self.__dict__[e]) + "/" + str(
                        self.default_level_size * self.level) + '\n'
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
            if len(self._inventory) + 1 <= self.default_inventory_size:
                self._inventory.append(elem)

            elif len(self._inventory) > Hero.default_inventory_size:
                the_game().add_message("You don't have enough space in your inventory")

    def check_inventory_size(self):
        if len(self._inventory) > Hero.default_inventory_size:
            the_game().add_message("Inventory full. Delete an item to gain space")
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
        if len(self._inventory) >= 0:
            if elem in self._inventory:
                self._inventory.remove(elem)
                if throwing:
                    the_game().add_message(f"You have successfully thrown the item : {elem.name}")
                else:
                    the_game().add_message(f"You have successfully deleted the item : {elem.name}")
            elif elem in self.weapon_slot:
                self.weapon_slot.remove(elem)
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
        self.level_step = self.default_level_size * self.level
        level_won = 0

        if xp_to_use > self.level_step:
            while xp_to_use > self.level_step:
                xp_to_use -= self.level_step

                self.gain_level(1)

                self.level_step = self.default_level_size * self.level
                level_won += 1

            self.xp = xp_to_use
            the_game().add_message("You won {0} level(s) and are now level {1}".format(level_won, self.level))

    def gain_level(self, nb_of_level):
        self.level += 1
        self.strength += nb_of_level
        self.gold += nb_of_level + self.level

        the_game().add_message(
            "You now have a strength of {0} and won {1} gold coins".format(self.strength, self.level))

    def check_stomach(self):
        cool_down_value = 5
        if self.stomach == 0:
            if not hasattr(Hero.check_stomach, "cool_down"):
                setattr(Hero.check_stomach, "cool_down", cool_down_value)
            else:
                if Hero.check_stomach.cool_down == 0:
                    self.hp -= 1
                    Hero.check_stomach.cool_down = cool_down_value - 1
                    the_game().add_message("WARNING : No more food !")
                else:
                    Hero.check_stomach.cool_down -= 1

    def buy(self, o):
        if isinstance(o, Equipment):
            if self.check_inventory_size():
                if self.gold >= o.price:
                    self.gold -= o.price
                    self.take(o)
                    the_game().add_message(f'You bought {o.name} for {o.price} gold')
                else:
                    the_game().add_message(f'Not enough gold. {o.price - self.gold} more gold needed')

    @staticmethod
    def choose_direction():
        the_game().add_message("Choose a direction to orientate yourself using the keys to move")
        the_game().gv.draw_message(200)
        pygame.display.update()

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
                        the_game().gv.inventory_on = False
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
                hit = False
                # Verify that the item is a weapon
                if isinstance(item, Weapon):
                    things_on_next_cell.hp -= item.launching_damage
                    hit = True
                    if things_on_next_cell.hp <= 0:
                        self.gain_xp(creature_xp=things_on_next_cell.xp)
                        the_game().floor.rm(the_game().floor.pos(things_on_next_cell))
                        the_game().add_message(f"[{things_on_next_cell.name}] has been killed using {item.name}")
                # If this item is not a weapon, use the item on the creature encountered
                else:
                    item.use(things_on_next_cell, monster=True)
                # If it is not the first throw, the item has been placed on the map and needs to be removed
                if i != 0:
                    the_game().floor.rm(the_game().floor.pos(item))
                # The item is removed from the inventory only if he doesn't come back
                if not item.come_back:
                    self.delete_item(item, True)
                # If a creature has been hit it appears in the game chat
                if hit:
                    the_game().add_message(f"[{things_on_next_cell.name}] lost {item.launching_damage} hp")
                break

            # Verify that the item encounter an equipment
            elif isinstance(things_on_next_cell, Equipment) or isinstance(things_on_next_cell, RoomObject):
                # If it is the first movement of the throw it can't be placed
                if i == 0:
                    the_game().add_message("You can't throw the item in this direction")
                else:
                    # The item is removed from the inventory only if he doesn't come back
                    if not item.come_back:
                        self.delete_item(item, True)
                    # The item is removed from the map if he comes back
                    else:
                        the_game().floor.rm(the_game().floor.pos(item))
                        the_game().add_message(f"The {item.name} came back to it's owner")
                break

            # Verify that the item encounter something different from the floor
            elif things_on_next_cell != the_game().floor.ground:
                if i == 0:
                    the_game().add_message("You can't throw the item in this direction")
                else:
                    # The item is removed from the inventory only if he doesn't come back
                    if not item.come_back:
                        self.delete_item(item, True)
                    # The item is removed from the map is he comes back
                    else:
                        the_game().floor.rm(the_game().floor.pos(item))
                        the_game().add_message(f"The {item.name} came back to it's owner")
                break

            # Verify that the item encounters a floor cell
            elif things_on_next_cell == the_game().floor.ground:
                # If it is the first movement, just place the item
                if i == 0:
                    the_game().floor.put(item_coord, item)
                # If the item reach the max distance...
                elif i == distance - 1:
                    # ... and can come back, delete it from the map, add text in game chat
                    if item.come_back:
                        the_game().floor.rm(the_game().floor.pos(item))
                        the_game().add_message(f"The {item.name} came back to it's owner")
                    # ... and can't come back, delete it from the inventory
                    else:
                        self.delete_item(item, True)

                # If the item can continue, move it in it's direction
                else:
                    the_game().floor.move(item, direction)

            else:
                raise NotImplementedError("Error might be due to an object not being managed.")


class Effect(object):

    def __init__(self, creature):
        self.game = the_game()
        self.creature = creature
        self.value = 0
        self.info = ""
        self.duration = None
        self.level = 0

        image = CG.get_image('Effects/' + self.name + '.png')  # change
        self.graphicOutput = pygame.transform.scale(image, (32, 32))

    def delete(self):
        try:
            self.game.active_effects.remove(self)
            del self
        except ValueError:
            pass

    def update(self):
        if isinstance(self, EphemeralEffect):
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

    @staticmethod
    def clear(unique=True):
        effects_to_delete = []
        for effect in the_game().active_effects:
            if effect.creature is the_game().hero:
                effects_to_delete.append(effect)

        for effect in effects_to_delete:
            Effect.delete(effect)

        return unique


class EphemeralEffect(Effect):

    def __init__(self, creature, duration, level):
        super().__init__(creature)
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
            self.info = f"[{self.creature.name}] {self.name} effect disappeared"
        super().deactivate()


class HealEffect(EphemeralEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "Recovering hp : +"

    def __init__(self, creature, duration, level):
        self.name = "Heal"
        super().__init__(creature, duration, level)
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

    def __init__(self, creature, duration, level):
        self.name = "Poison"
        super().__init__(creature, duration, level)
        self.value = self.level * PoisonEffect.LEVEL_FACTOR

    def action(self):
        self.creature.hp -= self.value
        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {PoisonEffect.DESCRIPTION}{self.value}"

        if self.creature.hp == 0:
            the_game().floor.rm(the_game().floor.pos(self.creature))
            super().deactivate(True)
        else:
            super().action()


class FeedEffect(EphemeralEffect):
    """
    Effect used to feed the hero. Creatures don't have a stomach so they can't be applied this effect.
    """
    LEVEL_FACTOR = 1
    DESCRIPTION = "I'm eating : +"

    def __init__(self, creature, duration, level):

        if isinstance(creature, Hero):
            self.name = "Feed"
            super().__init__(creature, duration, level)
            self.value = self.level * FeedEffect.LEVEL_FACTOR

    def action(self) -> None:
        if self.creature.default_stomach_size > self.creature.stomach + self.value:
            self.creature.stomach += self.value
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {FeedEffect.DESCRIPTION}{self.value}"

        else:
            self.creature.stomach = self.creature.default_stomach_size
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | Max food : {self.creature.stomach}/{self.creature.stomach}"

        super().action()


class HungerEffect(EphemeralEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION = "I'm hungry : -"

    def __init__(self, creature, duration, level):
        if isinstance(creature, Hero):
            self.name = "Hunger"
            super().__init__(creature, duration, level)
            self.value = self.level * HungerEffect.LEVEL_FACTOR

    def action(self):
        if isinstance(self.creature, Hero):
            self.creature.stomach -= self.value
            self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {HungerEffect.DESCRIPTION}{self.value}"
            super().action()


class TeleportEffect(EphemeralEffect):  # IS AN INSTANT EFFECT

    DESCRIPTION = "You have been teleported"

    def __init__(self, creature, duration=1):
        self.name = "Teleportation"
        super().__init__(creature, duration, 0)

    def action(self):
        """Teleport the creature"""
        r = the_game().floor.rand_room()
        c = r.rand_coord()

        while not the_game().floor.get(c) == Map.ground:
            c = r.rand_coord()
        the_game().floor.rm(the_game().floor.pos(self.creature))
        the_game().floor.put(c, self.creature)

        self.info = f"The creature <{self.creature.name}> has been teleported"


# CONSTANT EFFECTS

class ConstantEffect(Effect):

    def __init__(self, creature):
        super().__init__(creature)
        self.has_been_activated = False

    def activate(self, unique=True):
        if not self.has_been_activated:
            super().activate()
            self.has_been_activated = True

        return unique

    def deactivate(self):
        self.info += f" [{self.creature.name}] {self.name} effect disappeared"
        super().deactivate()


class StrengthEffect(ConstantEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION_ACTIVATE = "I feel stronger : +"
    DESCRIPTION_DEACTIVATE = "<End of boost> I feel weaker : -"

    def __init__(self, creature, duration=None, level=1):
        self.name = "Strength"
        super().__init__(creature)
        self.duration = duration
        self.level = level
        self.value = self.level * StrengthEffect.LEVEL_FACTOR

    def action(self):
        self.creature.strength += self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {StrengthEffect.DESCRIPTION_ACTIVATE}{self.value}"
        super().action()

    def activate(self, unique=True):
        if not self.has_been_activated:
            super().activate(unique)
        super().update()
        return unique

    def deactivate(self):
        self.creature.strength -= self.value
        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {StrengthEffect.DESCRIPTION_DEACTIVATE}{self.value}"
        super().deactivate()


class WeaknessEffect(ConstantEffect):
    LEVEL_FACTOR = 1
    DESCRIPTION_ACTIVATE = "I feel weaker : -"
    DESCRIPTION_DEACTIVATE = "<End of malus> I feel stronger : +"

    def __init__(self, creature, duration=None, level=1):
        self.name = "Weakness"
        super().__init__(creature)
        self.duration = duration
        self.level = level
        self.value = self.level * WeaknessEffect.LEVEL_FACTOR

    def action(self):
        self.creature.strength -= self.value

        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {WeaknessEffect.DESCRIPTION_ACTIVATE}{self.value}"
        super().action()

    def activate(self, unique=True):
        if not self.has_been_activated:
            super().activate(unique)
        super().update()
        return unique

    def deactivate(self):
        self.creature.strength += self.value
        self.info = f"[{self.creature.name}] | {self.name}<{self.level}> | {WeaknessEffect.DESCRIPTION_DEACTIVATE}{self.value}"
        super().deactivate()


# EQUIPMENT
class Equipment(Element):
    """A piece of equipment"""

    def __init__(self, name, abbreviation="", usage=None, durability=None, price=1):
        Element.__init__(self, name, abbreviation)
        self.usage = usage
        self.durability = durability
        self.price = price

        self.come_back = False

        # GRAPHICS
        image = CG.get_item_image(self.name)
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
            try:
                return self.usage(self, creature)
            except AttributeError:
                pass


class Weapon(Equipment):
    """A weapon which can be used by the Hero or the monsters"""

    def __init__(self, name, abbreviation="", price=1, damage=1, launching_damage=1, come_back=False):
        Equipment.__init__(self, name, abbreviation, price)
        self.damage = damage
        self.launching_damage = launching_damage
        self.come_back = come_back  # The weapon can come back to the hero when used (like a boomerang)


class Room(object):
    """A rectangular room in the map"""

    def __init__(self, c1, c2, special_objects=None):
        self.c1 = c1
        self.c2 = c2
        if special_objects is None:
            special_objects = []
        self.specialObjects = special_objects

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

    def rand_empty_middle_coord(self, map):
        """Same as rand_empty_coord but surrounded by ground"""
        list_of_coord_available = []
        for y in range(self.c1.y + 1, self.c2.y):
            for x in range(self.c1.x + 1, self.c2.x):
                c = Coord(x, y)
                if c.empty_around(map) and c != self.center():
                    list_of_coord_available.append(c)
        if len(list_of_coord_available) == 0:
            return self.rand_coord()
        else:
            return random.choice(list_of_coord_available)

    def decorate(self, map):
        """Decorates the room by adding a random equipment and monster."""
        for elem in self.specialObjects:
            map.put(self.rand_empty_middle_coord(map), elem)
        map.put(self.rand_empty_coord(map), the_game().rand_equipment(map.floor_number))
        map.put(self.rand_empty_coord(map), the_game().rand_monster(map.floor_number))


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

    empty = e = ' '  # A non walkable cell
    sizeFactor = round(16 * 1.25)

    def __init__(self, size=20, hero=None, put_hero=True, floor_number=None, special_room=None):
        self._mat = []
        self._elem = {}
        self._rooms = []
        self._rooms_to_reach = []
        self.floor_number = floor_number
        self.special_room = special_room

        for i in range(size):
            self._mat.append([Map.empty] * size)
        if hero is None:
            hero = Hero()
        self.hero = hero
        self.generate_rooms(7)
        self.reach_all_rooms()

        # Graphics

        self.graphic_map = []
        CG.generate_graphic_map(self)
        self.graphic_elements = []

        for i in range(len(self.graphic_map)):
            self.graphic_elements.append([None] * len(self.graphic_map))

        self.put_room_objects()
        if put_hero:
            self.put(self._rooms[0].center(), hero)
            self.hero.x = self._rooms[0].center().x
            self.hero.y = self._rooms[0].center().y
        for r in self._rooms:
            r.decorate(self)

        self.update_elements(0)

    def add_room(self, room):
        """Adds a room in the map."""
        self._rooms_to_reach.append(room)
        for y in range(room.c1.y, room.c2.y + 1):
            for x in range(room.c1.x, room.c2.x + 1):
                self._mat[y][x] = Map.ground

    def find_room(self, coord):
        """If the coord belongs to a room, returns the room elsewhere returns None"""
        for r in self._rooms_to_reach:
            if coord in r:
                return r
        return None

    def intersect_none(self, room):
        """Tests if the room shall intersect any room already in the map."""
        for r in self._rooms_to_reach:
            if room.intersect(r):
                return False
        return True

    def dig(self, coord):
        """Puts a ground cell at the given coord.
            If the coord corresponds to a room, considers the room reached."""
        self._mat[coord.y][coord.x] = Map.ground
        r = self.find_room(coord)
        if r:
            self._rooms_to_reach.remove(r)
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
        room_a = random.choice(self._rooms)
        room_b = random.choice(self._rooms_to_reach)

        self.corridor(room_a.center(), room_b.center())

    def reach_all_rooms(self):
        """Makes all rooms reachable.
            Start from the first room, repeats @reach until all rooms are reached."""
        self._rooms.append(self._rooms_to_reach.pop(0))
        while len(self._rooms_to_reach) > 0:
            self.reach()

    def put_room_objects(self):
        for key in Game._room_objects:
            if key == "downstair" and self.floor_number > 0:
                r = random.choice(self._rooms)
                r.specialObjects.append(Game._room_objects[key])
            if key == "upstair" and self.floor_number + 1 < the_game().nb_floors:
                r = random.choice(self._rooms)
                r.specialObjects.append(Game._room_objects[key])

    def rand_room(self):
        """A random room to be put on the map."""
        c1 = Coord(random.randint(0, len(self) - 3), random.randint(0, len(self) - 3))
        c2 = Coord(min(c1.x + random.randint(3, 8), len(self) - 1), min(c1.y + random.randint(3, 8), len(self) - 1))
        return Room(c1, c2)

    def generate_rooms(self, n):
        """Generates n random rooms and adds them if non-intersecting."""
        if self.special_room is not None:
            self.add_room(Game._special_rooms_list[self.special_room])
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

    def in_graphic_map(self, c):
        return 0 <= c.x < len(self.graphic_map) and 0 <= c.y < len(self.graphic_map)

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

    def check_move(self, e, way):
        """Returns element in way"""
        orig = self.pos(e)
        dest = orig + way
        if dest in self:
            return self.get(dest)
        return self.empty

    def direction(self, c1, c2):
        """Returns the direction between two coordinates."""
        final_way = Coord(0, 0)
        for i in range(-1, 2):
            for j in range(-1, 2):
                way = Coord(i, j)
                in_map = 0 <= c1.x + way.x < len(self._mat) and 0 <= c1.y + way.y < len(self._mat)
                if in_map and (c1 + way).distance(c2) < (c1 + final_way).distance(c2) and (self.get(
                        c1 + way) == self.ground or self.get(c1 + way) == self.hero):
                    final_way = way
        return final_way

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

    def update_elements(self, state):
        clear_list(self.graphic_elements)
        for y in range(len(self._mat)):
            for x in range(len(self._mat)):

                elem = self.get(Coord(x, y))
                if elem != self.ground and elem != self.empty:
                    if isinstance(elem, Hero):
                        elem.x = x
                        elem.y = y
                    elif isinstance(elem, Creature):
                        self.graphic_elements[y][x] = elem.graphicOutput[state]
                    elif isinstance(elem, Equipment):
                        self.graphic_elements[y][x] = elem.graphicOutput[0]
                    elif isinstance(elem, RoomObject):
                        if len(elem.graphicOutput) == 2:
                            self.graphic_elements[y][x] = elem.graphicOutput[state]
                        else:
                            self.graphic_elements[y][x] = elem.graphicOutput[0]
        the_game().gv.update_fog(self)


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
        self.frame_count = 0
        self.monster_state = 0

        self.stop = False
        self.choice = 0
        self.choice_inv = 0
        self.newRound = False

        # Messages
        self.game_font = None
        self.menu_font = None
        self._msg = []

        self.qwerty = False

        self.options_menu_start = [("Menu", False), ("", False), ("New Game", True), ("Preferences", True),
                                   ("Exit Game", True)]
        self.options_menu = [("Menu", False), ("", False), ("Resume Game", True), ("Preferences", True),
                             ("Exit Game", True)]
        self.options_hero = [("Characters", False), ("", False), ("Template", True), ("Rogue", True),
                             ("Engineer", True), ("Warrior", True), ("Mage", True), ("Paladin", True)]
        self.options_controls = [
            ("i : open/close inventory", False),
            ("k : suicide", False),
            ("t : delete item", False),
            ("b : select weapon", False),
            ("n : remove current weapon", False),
            ("l : launch from weapon slot", False),
            ("u / Enter : use item selected", False),
            ("Return", True)]
        self.options_preferences = [('Preferences', False),
                                    ('', False),
                                    ('Show Controls', True),
                                    ('Set Qwerty', True),
                                    ('Set Azerty', True),
                                    ('Choose Character', True),
                                    ('', False),
                                    ('Return', True)]
        self.options_game_over = [("-- Game Over --", False), ("", False), ("Exit Game", True)]

        # Menu
        self.menu_on = True
        self.inventory_on = False
        self.list_menu = self.options_menu_start
        self.colour_menu = (140, 140, 150)

        # Game Surfaces
        self.explosion = []
        for i in range(6):
            image = CG.get_image("Animations/explosion-" + str(i) + ".png")
            self.explosion.append(pygame.transform.scale(image, (40, 40)))

        self.hearts = []
        for i in range(5):
            image1 = CG.get_image("GUI/heart" + str(i) + "-0.png")
            image2 = CG.get_image("GUI/heart" + str(i) + "-1.png")
            self.hearts.append([image1, image2])

        self.black_hearts = []
        for i in range(5):
            image1 = CG.get_image("GUI/blackheart" + str(i) + "-0.png")
            image2 = CG.get_image("GUI/blackheart" + str(i) + "-1.png")
            self.black_hearts.append([image1, image2])

        self.xp_bord = []
        for i in range(3):
            self.xp_bord.append(CG.get_image("GUI/bordexp" + str(i) + ".png"))

        self.blockSpace = pygame.transform.scale(CG.get_image("GUI/blockSpace.png"), (32, 32))
        self.fog = CG.get_image("Background/Void.png")

        self.food = [CG.get_image("GUI/food0.png"), CG.get_image("GUI/food1.png")]
        self.dollar = CG.get_image("GUI/dollar.png")
        self.arrow = CG.get_image("GUI/arrow.png")

        # Music effects
        self._songs = ['song-1.mp3', 'song-2.mp3', 'song-3.mp3']

    def draw_gui(self, state):
        self.screen.fill((72, 62, 87), (self.width / 2, 0, self.width / 2, self.height))

        # Draw Character
        scale = round(self.height / 5)
        hero_image = pygame.transform.scale(self.hero.graphicOutput, (scale, scale))
        hero_drawing_x = (self.width / 2) * (1 + 1 / 10)
        self.screen.blit(hero_image, (hero_drawing_x, self.height / 10))
        h_d_width = 200

        # Draw hearts
        for i in range(Hero.default_hp):
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

            self.screen.blit(image, (hero_drawing_x + h_d_width + 18 * i, self.height * 3 / 20))

        # Draw food
        for i in range(Hero.default_stomach_size):
            if self.hero.stomach - i > 0:
                self.screen.blit(self.food[0], (hero_drawing_x + h_d_width + 18 * i, self.height * 3 / 20 + 25))
            else:
                self.screen.blit(self.food[1], (hero_drawing_x + h_d_width + 18 * i, self.height * 3 / 20 + 25))

        # Draw xp
        xp_percentage = self.hero.xp * 100 / self.hero.level_step

        self.screen.fill((0, 255, 0), (hero_drawing_x + h_d_width, self.height * 3 / 20 + 56, xp_percentage * 2, 6))

        for i in range(11):
            if i == 0:
                self.screen.blit(self.xp_bord[0],
                                 (hero_drawing_x + h_d_width + 18 * i, self.height * 3 / 20 + 50))
            elif i == 10:
                self.screen.blit(self.xp_bord[2],
                                 (hero_drawing_x + h_d_width + 18 * i, self.height * 3 / 20 + 50))
            else:
                self.screen.blit(self.xp_bord[1],
                                 (hero_drawing_x + h_d_width + 18 * i, self.height * 3 / 20 + 50))

        # Draw Hero Level
        text = self.game_font.render('Level: ' + str(self.hero.level), True, (0, 0, 0))
        self.screen.blit(text, (hero_drawing_x + h_d_width, self.height * 3 / 20 - 58))

        # Draw Hero Strength
        text = self.game_font.render('Strength: ' + str(self.hero.strength), True, (0, 0, 0))
        self.screen.blit(text, (hero_drawing_x + h_d_width, self.height * 3 / 20 - 30))

        # Draw gold
        self.screen.blit(self.dollar, (hero_drawing_x + h_d_width, self.height * 3 / 20 + 75))
        text = self.game_font.render(str(self.hero.gold), True, (0, 0, 0))
        self.screen.blit(text, (hero_drawing_x + h_d_width + 30, self.height * 3 / 20 + 76))

        # Effects
        for i, x in enumerate(the_game().active_effects):
            if x.creature == self.hero:
                self.screen.blit(x.graphicOutput, (hero_drawing_x + h_d_width + 32 * i, self.height * 3 / 20 + 100))

        # Inventory
        sf = 2
        case = 16

        self.screen.blit(self.blockSpace, (self.width / 2 * (1 + 1 / 10) + 65, self.height * 7 / 20))
        if len(self.hero.weapon_slot) != 0:
            self.screen.blit(self.hero.weapon_slot[0].graphicOutput[1],
                             (self.width / 2 * (1 + 1 / 10) + 65, self.height * 7 / 20))

        for i in range(Hero.default_inventory_size):
            self.screen.blit(self.blockSpace, (self.width / 2 * (1 + 3 / 10) + case * i * sf, self.height * 7 / 20))
            if i < len(self.hero._inventory):
                if sf != 1:
                    image = pygame.transform.scale(self.hero._inventory[i].graphicOutput[1], (16 * sf, 16 * sf))
                else:
                    image = self.hero._inventory[i].graphicOutput[1]
                self.screen.blit(image, (self.width / 2 * (1 + 3 / 10) + case * i * sf, self.height * 7 / 20))

        # Arrow Inventory
        if self.inventory_on:
            if len(self.hero._inventory) != 0:
                self.choice_inv %= len(self.hero._inventory)
            else:
                self.choice_inv = 0
            if sf != 2:
                image = pygame.transform.scale(self.arrow, (16 * sf, 16 * sf))
            else:
                image = self.arrow
            self.screen.blit(image, (
                self.width / 2 * (1 + 3 / 10) + 7 + case * self.choice_inv * sf, self.height * 7 / 20 - 21))

    def draw_map(self):
        self.screen.fill((80, 74, 85), (0, 0, self.width / 2, self.height))
        for y in range(self.height // Map.sizeFactor):
            for x in range(self.width // (2 * Map.sizeFactor)):
                self.screen.blit(self.fog, (x * Map.sizeFactor, y * Map.sizeFactor))

        for y in range(len(self.floor.graphic_map)):
            for x in range(len(self.floor.graphic_map[y])):
                pos = (Map.sizeFactor * x + self.orig_x, Map.sizeFactor * y + self.orig_y)
                if self.floor.graphic_map[y][x][1]:
                    self.screen.blit(self.floor.graphic_map[y][x][0], pos)
                else:
                    self.screen.blit(self.fog, pos)

        # Draw Map level
        string = f"Floor number: {the_game().floor_list[the_game().actual_floor].floor_number + 1} / {the_game().nb_floors}"
        text = self.game_font.render(string, True, (0, 0, 0))

        text_width, text_height = self.game_font.size(string)
        self.screen.fill((72, 62, 87), (45, self.orig_y / 3 - 5, text_width + 10, text_height + 10))
        self.screen.blit(text, (50, self.orig_y / 3))

    def draw_elements(self, monster_state):
        self.floor.update_elements(monster_state)
        for y in range(len(self.floor.graphic_elements)):
            for x in range(len(self.floor.graphic_elements)):
                case = self.floor.graphic_elements[y][x]
                if case is not None and self.floor.graphic_map[y][x][1]:
                    if isinstance(self.floor._mat[y][x], RoomObject):
                        if self.floor._mat[y][x].name == "upstair":
                            relief = 20
                        else:
                            relief = 0
                    else:
                        relief = Map.sizeFactor / 4
                    self.screen.blit(case,
                                     (Map.sizeFactor * x + self.orig_x, Map.sizeFactor * y + self.orig_y - relief))

    def draw_message(self, time):
        # Draw Message self.screen
        self.screen.fill((20, 12, 28), (
            (self.width / 2) * (1 + 1 / 8), self.height * 3 / 4, (self.width / 2) * 6 / 8, self.height / 5))
        b = 5
        self.screen.fill((140, 140, 150), (
            (self.width / 2) * (1 + 1 / 8) + b, self.height * 3 / 4 + b, (self.width / 2) * 6 / 8 - 2 * b,
            self.height / 5 - 2 * b))

        new_msg = the_game().read_messages()
        nb_lines = len(self._msg)
        msg_nuls = []
        for k in new_msg:
            self._msg.append([k, time])
            if len(self._msg) > 5:
                self._msg.pop(0)
        for i in range(nb_lines):
            self.screen.blit(self._msg[i][0],
                             ((self.width / 2) * (1 + 1 / 8) + 15, self.height * 3 / 4 + 5 + 20 * i + 10))
            self._msg[i][1] -= 1
            if self._msg[i][1] <= 0:
                msg_nuls.append(i)

        for j in msg_nuls:
            if j < len(self._msg):
                self._msg.pop(j)

    def draw_menu(self, list_menu, colour=(140, 140, 150)):
        menu_y = self.height / 6
        self.screen.fill((255, 255, 51), (self.width / 4, menu_y, self.width / 2, self.height * 4 / 6))
        b = 5
        self.screen.fill(colour,
                         (self.width / 4 + b, self.height / 6 + b, self.width / 2 - 2 * b, self.height * 4 / 6 - 2 * b))

        self.choice %= len(list_menu)

        for i in range(len(list_menu)):
            if i == self.choice:
                if list_menu[i][1]:
                    f = ">>   "
                else:
                    f = "  "
                    self.choice = (self.choice + 1) % len(list_menu)
            else:
                f = "  "
            current_item = list_menu[i][0]
            if isinstance(current_item, Weapon):
                if current_item.come_back:
                    to_add = "(comes back)"
                else:
                    to_add = ""
                objet = f"{current_item.name} [ {str(current_item.price)} $ ]   < dmg = {current_item.damage}, launch dmg = {current_item.launching_damage} >" + to_add
            elif isinstance(current_item, Equipment):
                objet = f"{current_item.name} [ {str(current_item.price)} $ ]"
            else:
                objet = current_item

            o_height = self.menu_font.size(objet)[1]
            text = self.menu_font.render(f + objet, True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.width / 2, menu_y + (i + 1) * (o_height - 15)))
            self.screen.blit(text, text_rect)

    def draw_trader(self, list_objects):
        lm = [('Do you want something ?', False), ('', False)]

        for o in list_objects:
            lm.append((o, True))
        lm += [('', False), ('Maybe Later', True)]

        self.list_menu = lm
        self.colour_menu = (30, 212, 157)
        self.menu_on = True

    def draw_hero_move(self):
        h = self.hero
        sf = Map.sizeFactor
        persp = -sf / 4

        has_moved = False

        way = Coord(0, 0)
        if h.moving_UDLR[0]:
            # UP
            way += Coord(0, -1)
        elif h.moving_UDLR[1]:
            # DOWN
            way += Coord(0, 1)
        elif h.moving_UDLR[2]:
            # LEFT
            way += Coord(-1, 0)
        elif h.moving_UDLR[3]:
            # RIGHT
            way += Coord(1, 0)
        elif h.moving_UDLR[4]:
            # UP LEFT
            way += Coord(-1, -1)
        elif h.moving_UDLR[5]:
            # UP RIGHT
            way += Coord(1, -1)
        elif h.moving_UDLR[6]:
            # DOWN RIGHT
            way += Coord(1, 1)
        elif h.moving_UDLR[7]:
            # DOWN LEFT
            way += Coord(-1, 1)

        if way != Coord(0, 0):

            elem_in_way = self.floor.check_move(h, way)
            if elem_in_way == self.floor.ground:
                pos = (sf * h.x + way.x * h.state * sf / 4 + self.orig_x,
                       sf * h.y + way.y * h.state * sf / 4 + self.orig_y + persp)

                self.screen.blit(h.animationUDLR[way.get_tuple()][h.state], pos)
                h.state += 1
                has_moved = True

                if h.state >= 4:
                    h.state = 0
                    self.floor.move(h, way)
                    self.newRound = True

                    if self.stop:
                        h.moving_UDLR = [False] * 8
                        self.stop = False

            elif isinstance(elem_in_way, Creature):
                self.floor.move(h, way)
                self.newRound = True

                for i in range(6):
                    self.screen.blit(self.explosion[i], (
                        sf * (h.x + way.x) + self.orig_x - 12, sf * (h.y + way.y) + self.orig_y + persp - 12))
                    self.screen.blit(h.graphicOutput, (sf * h.x + self.orig_x, sf * h.y + self.orig_y + persp))
                    pygame.display.update()
                    pygame.time.delay(50)

            elif isinstance(elem_in_way, Element):
                self.floor.move(h, way)

        if not has_moved:
            self.screen.blit(h.graphicOutput, (sf * h.x + self.orig_x, sf * h.y + self.orig_y + persp))

    def player_plays(self, event):
        do = False
        keydown_bool = False

        if event.type == pygame.KEYDOWN:
            keydown_bool = True
            do = True
        elif event.type == pygame.KEYUP:
            keydown_bool = False
            do = True

        # Movement
        if do:

            if keydown_bool or self.hero.state == 0:
                self.hero.moving_UDLR = [False] * 8

                if self.qwerty:  # change
                    if event.key == pygame.K_w:  # UP
                        self.hero.moving_UDLR[0] = keydown_bool
                    if event.key == pygame.K_x:  # DOWN
                        self.hero.moving_UDLR[1] = keydown_bool
                    elif event.key == pygame.K_a:  # LEFT
                        self.hero.moving_UDLR[2] = keydown_bool
                    elif event.key == pygame.K_d:  # RIGHT
                        self.hero.moving_UDLR[3] = keydown_bool

                    # Diagonales
                    elif event.key == pygame.K_q:  # UP LEFT
                        self.hero.moving_UDLR[4] = keydown_bool
                    elif event.key == pygame.K_e:  # UP RIGHT
                        self.hero.moving_UDLR[5] = keydown_bool
                    elif event.key == pygame.K_c:  # DOWN RIGHT
                        self.hero.moving_UDLR[6] = keydown_bool
                    elif event.key == pygame.K_z:  # DOWN LEFT
                        self.hero.moving_UDLR[7] = keydown_bool
                else:
                    if event.key == pygame.K_z:  # UP
                        self.hero.moving_UDLR[0] = keydown_bool
                    if event.key == pygame.K_x:  # DOWN
                        self.hero.moving_UDLR[1] = keydown_bool
                    elif event.key == pygame.K_q:  # LEFT
                        self.hero.moving_UDLR[2] = keydown_bool
                    elif event.key == pygame.K_d:  # RIGHT
                        self.hero.moving_UDLR[3] = keydown_bool

                    # Diagonals
                    elif event.key == pygame.K_a:  # UP LEFT
                        self.hero.moving_UDLR[4] = keydown_bool
                    elif event.key == pygame.K_e:  # UP RIGHT
                        self.hero.moving_UDLR[5] = keydown_bool
                    elif event.key == pygame.K_c:  # DOWN RIGHT
                        self.hero.moving_UDLR[6] = keydown_bool
                    elif event.key == pygame.K_w:  # DOWN LEFT
                        self.hero.moving_UDLR[7] = keydown_bool

                if event.key == pygame.K_UP:  # UP
                    self.hero.moving_UDLR[0] = keydown_bool
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:  # DOWN
                    self.hero.moving_UDLR[1] = keydown_bool
                elif event.key == pygame.K_LEFT:  # LEFT
                    self.hero.moving_UDLR[2] = keydown_bool
                elif event.key == pygame.K_RIGHT:  # RIGHT
                    self.hero.moving_UDLR[3] = keydown_bool

                # Actions
                if keydown_bool:
                    self.choose_action(event)

            else:
                self.stop = True

    def choose_action(self, event):
        if event.key == pygame.K_k:
            Game._actions['k'](self.hero)
        elif event.key == pygame.K_b:
            Game._actions['b'](self.hero)
        elif event.key == pygame.K_n:
            Game._actions['n'](self.hero)
        elif event.key == pygame.K_l:
            Game._actions['l'](self.hero)

    def choose_in_menu(self, event):
        move_choice = 0
        if self.qwerty:
            if event.key == pygame.K_w:
                move_choice = - 1
            elif event.key == pygame.K_s:
                move_choice = 1
        else:
            if event.key == pygame.K_z:
                move_choice = - 1
            elif event.key == pygame.K_s:
                move_choice = 1

        if event.key == pygame.K_UP:
            move_choice = - 1
        elif event.key == pygame.K_DOWN:
            move_choice = 1

        for i in range(len(self.list_menu)):
            self.choice += move_choice
            self.choice %= len(self.list_menu)
            if self.list_menu[self.choice][1]:
                break

        if event.key == pygame.K_RETURN:

            this_choice = self.list_menu[self.choice][0]

            if this_choice == "New Game":
                self.menu_on = not self.menu_on
                self.list_menu = self.options_menu

            elif this_choice == "Resume Game" or this_choice == 'Maybe Later':
                self.menu_on = not self.menu_on

            elif this_choice == "Exit Game":
                self.running = False

            elif this_choice == "Choose Character":
                self.list_menu = self.options_hero
                self.choice = 0

            elif self.list_menu[self.choice] in self.options_hero:
                self.change_hero_appearance(this_choice)
                self.choice = 0
                self.list_menu = self.options_menu


            elif this_choice == "Show Controls":
                self.list_menu = self.options_controls

            elif this_choice == "Return":
                self.list_menu = self.options_menu

            elif this_choice == "Preferences":
                self.list_menu = self.options_preferences


            elif this_choice == "Set Qwerty":
                self.qwerty = True
                self.choice = 0
                self.list_menu = self.options_menu

            elif this_choice == "Set Azerty":
                self.qwerty = False
                self.choice = 0
                self.list_menu = self.options_menu

            # Marchand

            elif isinstance(this_choice, Equipment):
                self.hero.buy(this_choice)
                self.menu_on = False

    def choose_in_inventory(self, event):

        if self.qwerty:
            if event.key == pygame.K_a:
                self.choice_inv -= 1
            elif event.key == pygame.K_d:
                self.choice_inv += 1

        else:
            if event.key == pygame.K_q:
                self.choice_inv -= 1
            elif event.key == pygame.K_d:
                self.choice_inv += 1

        if event.key == pygame.K_LEFT:
            self.choice_inv -= 1
        elif event.key == pygame.K_RIGHT:
            self.choice_inv += 1

        # Use equipment
        if event.key == pygame.K_RETURN or event.key == pygame.K_u:
            Game._actions['u'](self.hero)
            self.inventory_on = False

        elif event.key == pygame.K_t:
            Game._actions["t"](self.hero)
            self.inventory_on = False

        elif event.key == pygame.K_b:
            Game._actions["b"](self.hero)
            self.inventory_on = False

        elif event.key == pygame.K_n:
            Game._actions["n"](self.hero)
            self.inventory_on = False

        elif event.key == pygame.K_l:
            the_game().hero.throw_item(the_game().gv.select_from_inventory(Equipment), 5)

        self.floor.update_elements(self.monster_state)

    def change_hero_appearance(self, costume):
        images = CG.get_hero_image(costume)
        self.hero.graphicOutput = images[0]

        images = CG.get_hero_image(costume)

        self.hero.graphicOutput = images[0]
        self.hero.animationUDLR = {(0, -1): images[12:16],  # cannot put Coord since it's not hashable

                                   (0, 1): images[:4],
                                   (-1, 1): images[:4],
                                   (1, 1): images[:4],

                                   (-1, 0): images[4:8],
                                   (-1, -1): images[4:8],

                                   (1, 0): images[8:12],
                                   (1, -1): images[8:12],

                                   }

    def select_from_inventory(self, item_chosen_class):
        if self.choice_inv < len(self.hero._inventory) and isinstance(self.hero._inventory[self.choice_inv],
                                                                      item_chosen_class):
            return self.hero._inventory[self.choice_inv]

        return None

    def draw_game_screen(self):
        self.draw_map()
        self.draw_elements(self.monster_state)
        self.draw_hero_move()

    def update_fog(self, actual_map):
        for o in [actual_map.hero, Game.monsters[20][0]]:
            if isinstance(o, Hero):
                x = self.hero.x
                y = self.hero.y
            else:
                c = actual_map.pos(o)
                if c is None:
                    break
                x = c.x
                y = c.y

            radius = 5

            for i in range(-radius, radius + 1):
                for j in range(-radius, radius + 1):
                    c = Coord(x + i, y + j)
                    if self.floor is not None and self.floor.in_graphic_map(c):
                        if Coord(x, y).distance(c) <= radius:
                            self.floor.graphic_map[y + j][x + i][1] = True

    def play_next_song(self):
        cle = 'Images/musiques/'
        self._songs = self._songs[1:] + [self._songs[0]]  # move current song to the back of the list
        pygame.mixer.music.load(cle + self._songs[0])
        pygame.mixer.music.play()


class Game(object):
    """ Class representing game state """

    """ available equipments """
    equipments = {0: [Equipment("gold", "o"),
                      Equipment("basic bread", "§", usage=lambda self, hero: FeedEffect.activate(
                          FeedEffect(hero, 1, hero.default_stomach_size))),
                      Equipment("hunger mushroom", "£",
                                usage=lambda self, hero: HungerEffect.activate(HungerEffect(hero, 3, 1))),
                      Equipment("poisonous mushroom", "%", price=2,
                                usage=lambda self, hero: PoisonEffect.activate(PoisonEffect(hero, 3, 1))),
                      ],
                  1: [Equipment("strength potion", "!", price=3,
                                usage=lambda self, hero: StrengthEffect.activate(
                                    StrengthEffect(hero, 10, 3))),
                      Equipment("weakness potion", "!", price=3,
                                usage=lambda self, hero: WeaknessEffect.activate(WeaknessEffect(hero, 10))),
                      Equipment("teleport potion", "!", price=3,
                                usage=lambda self, hero: TeleportEffect.activate(TeleportEffect(hero))),
                      Equipment("healing potion", "!", price=3,
                                usage=lambda self, hero: HealEffect.activate(HealEffect(hero, 1, 3))),
                      ],
                  2: [Equipment("milk", "m", price=4, usage=lambda self, hero: Effect.clear()),
                      ],
                  3: [Equipment("portoloin", "w", price=15,
                                usage=lambda self, hero: TeleportEffect.activate(TeleportEffect(hero),
                                                                                 False)),
                      Equipment("healing potion", "!", price=5,
                                usage=lambda self, hero: HealEffect.activate(HealEffect(hero, 1, 6))),
                      Equipment("strength potion", "!", price=5,
                                usage=lambda self, hero: StrengthEffect.activate(
                                    StrengthEffect(hero, 10, 10))),
                      ],
                  }

    """ available weapons """
    weapons = {
        0: [Weapon("Basic Sword", "†", price=2, damage=random.randint(2, 6), launching_damage=random.randint(1, 3))],
        1: [Weapon("Shuriken", "*", damage=random.randint(1, 2), launching_damage=random.randint(3, 5))],
        2: [Weapon("Boomerang", "¬", price=3, damage=random.randint(1, 2), launching_damage=random.randint(2, 3),
                   come_back=True)],
    }

    """ available monsters """
    monsters = {0: [Creature("Goblin", hp=4, xp=4),
                    Creature("Bat", hp=2, abbreviation="W", xp=2),
                    Creature("BabyDemon", hp=2, strength=2, xp=4)],
                1: [Creature("Ork", hp=4, strength=2, xp=10),
                    Creature("Blob", hp=10, xp=8),
                    Creature("Angel", hp=10, xp=4)],
                2: [Creature("Poisonous spider", hp=5, xp=10, strength=0, abbreviation="&",
                             powers_list=[[PoisonEffect, 3, 1]], cooldown=5),
                    Creature("BabyDemon", hp=2, strength=2, xp=4),
                    ],
                5: [Creature("Dragon", hp=20, strength=3, xp=50)],
                20: [Creature("Death", hp=50, strength=3, xp=100, abbreviation='ñ')]
                }

    """ available actions """
    _actions = {'k': lambda h: h.__setattr__('hp', 0),
                'u': lambda h: h.use(the_game().gv.select_from_inventory(Equipment)),
                ' ': lambda h: None,
                't': lambda hero: hero.delete_item(
                    the_game().gv.select_from_inventory(Equipment) if len(hero._inventory) > 0 else False),
                'b': lambda hero: hero.equip_weapon([x for x in hero._inventory if isinstance(x, Weapon)][0]) if any(
                    isinstance(elem, Weapon) for elem in hero._inventory) else the_game().add_message(
                    "You don't have any weapon in your inventory"),
                'n': lambda hero: hero.remove_current_weapon(),
                'l': lambda hero: hero.throw_item(hero.weapon_slot[0], 5) if len(hero.weapon_slot) != 0 else False,

                }

    _room_objects = {'upstair': RoomObject('upstair', "^", usage=lambda: RoomObject.go_upstair()),
                     'downstair': RoomObject('downstair', "v", usage=lambda: RoomObject.go_downstair()),
                     'marchand': RoomObject('marchand', "", usage=lambda: RoomObject.meet_trader()),
                     }

    _special_rooms_list = {"finalBoss": Room(Coord(1, 1), Coord(19, 10), [monsters[20][0]]),
                           'marchand': Room(Coord(15, 15), Coord(19, 19), [_room_objects['marchand']]),
                           }

    sizeFactor = Map.sizeFactor

    def __init__(self, level=1, hero=None, nb_floors=4):

        self.level = level
        self.active_effects = []
        self._message = []

        if hero is None:
            hero = Hero()
        self.hero = hero

        self.nb_floors = nb_floors
        self.floor_list = []
        self.actual_floor = 0
        self.floor = None

        self.number_of_round = 0
        self.apply_effects_bool = False

        # GRAPHICS
        self.gv = GraphicVariables(self.hero)

        self.paused = False

    def build_floor(self):
        """Creates a map for the current floor."""

        place_hero = True
        rand = random.randint(0, self.nb_floors - 2)

        for i in range(self.nb_floors):
            print('Building Floor ' + str(i + 1) + '/' + str(self.nb_floors))

            if i == rand:
                self.floor_list.append(
                    Map(hero=self.hero, put_hero=place_hero, floor_number=i, special_room='marchand'))
            elif i == self.nb_floors - 1:
                self.floor_list.append(
                    Map(hero=self.hero, put_hero=place_hero, floor_number=i, special_room='finalBoss'))
            else:
                self.floor_list.append(Map(hero=self.hero, put_hero=place_hero, floor_number=i))
            place_hero = False

        self.gv.floor = self.floor = self.floor_list[self.actual_floor]

    @staticmethod
    def rearrange_sentences(text_message, length_max=50):
        text_message_list = text_message.split(" ")

        res = []
        word_to_add = ""

        while len(text_message_list) != 0:

            if len(text_message_list[0]) > length_max:
                res.append(text_message_list[0][:length_max])
                word_to_recount = text_message_list[0][length_max + 1:]
                text_message_list.pop(0)
                word_to_add = word_to_recount + " " + word_to_add

            if len(word_to_add + text_message_list[0]) <= length_max:
                word_to_add += text_message_list.pop(0) + " "
                if len(text_message_list) == 0:
                    res.append(word_to_add)
            else:
                res.append(word_to_add)
                word_to_add = ""

        return res

    def add_message(self, msg):
        """Adds a message in the message list."""

        line_list = Game.rearrange_sentences(msg)
        for line_text in line_list:
            self._message.append(line_text)

    def read_messages(self):
        """Returns the message list and clears it."""
        renders = []
        for m in self._message:
            renders.append(self.gv.game_font.render(m, True, (0, 0, 0)))

        self._message.clear()
        return renders.copy()

    @staticmethod
    def rand_element(collect, floor_level):
        """Returns a clone of random element from a collection using exponential random law."""
        x = random.expovariate(1 / (floor_level + 1))
        for k in collect.keys():
            if k <= x:
                element_list = collect[k]
        return copy.copy(random.choice(element_list))

    def rand_equipment(self, floor_level):
        """Returns a random equipment."""
        return self.rand_element(Game.equipments, floor_level)

    def rand_monster(self, floor_level):
        """Returns a random monster."""
        return self.rand_element(Game.monsters, floor_level)

    def play_with_graphics(self):

        print("\n--- Initialising Graphics ---")
        print("Loading ...")

        self.build_floor()

        pygame.init()

        # Create the screen
        info_object = pygame.display.Info()
        height = self.gv.height = info_object.current_h - 60
        width = self.gv.width = info_object.current_w

        self.gv.orig_x = width / 4 - 10 * Map.sizeFactor
        self.gv.orig_y = height / 6

        self.gv.screen = pygame.display.set_mode((width, height))

        # Title and Icon
        pygame.display.set_caption("Rogue: Jaime et Raphael")
        icon = pygame.image.load("images/magicsword.png")
        pygame.display.set_icon(icon)

        # Font
        self.gv.game_font = pygame.font.SysFont('Agencyfc', 30)
        self.gv.menu_font = pygame.font.SysFont('papyrus', 40)

        # Music
        song_end = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(song_end)
        self.gv.play_next_song()

        # Initialize Brouillard
        self.gv.update_fog(self.floor)

        while self.gv.running:

            pygame.time.delay(50)

            if self.gv.frame_count > 10:
                self.gv.monster_state = opp(self.gv.monster_state)
                self.gv.frame_count = 0
            self.gv.frame_count += 1

            # Events
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.gv.running = False

                elif event.type == song_end:
                    self.gv.play_next_song()

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        self.gv.menu_on = not self.gv.menu_on
                        self.gv.list_menu = self.gv.options_menu
                        self.gv.colour_menu = (140, 140, 150)

                        self.gv.inventory_on = False

                    if self.gv.menu_on:
                        self.gv.choose_in_menu(event)

                    if event.key == pygame.K_i:
                        self.gv.inventory_on = not self.gv.inventory_on

                    if self.gv.inventory_on:
                        self.gv.choose_in_inventory(event)

                if not self.gv.inventory_on:
                    self.gv.player_plays(event)

            # Menu
            if self.gv.menu_on:
                self.gv.draw_menu(self.gv.list_menu, self.gv.colour_menu)

            else:
                # Background
                self.gv.draw_gui(self.gv.monster_state)

                if self.hero.hp <= 0:
                    # self.hero.hp = 1
                    self.gv.list_menu = self.gv.options_game_over
                    self.gv.menu_on = True

                self.hero.check_inventory_size()

                if self.gv.newRound:
                    self.gv.newRound = False
                    self.number_of_round += 1
                    self.apply_effects_bool = True
                    self.floor.move_all_monsters()

                    if self.number_of_round % 5 == 0 and self.hero.stomach == Hero.default_stomach_size:
                        self.hero.hp += 1
                        if self.hero.hp > self.hero.default_hp:
                            self.hero.hp -= 1

                    if self.number_of_round % 20 == 0 and self.hero.__dict__["stomach"] > 0:
                        self.hero.__dict__["stomach"] -= 1
                    self.hero.check_stomach()

                if self.apply_effects_bool:
                    if len(self.active_effects) != 0:
                        i = 0
                        while i < len(self.active_effects):
                            if not self.active_effects[i].update():
                                i += 1
                    self.apply_effects_bool = False

                # Messages
                self.gv.draw_message(200)

                self.gv.draw_game_screen()

            pygame.display.update()

        pygame.quit()


def the_game(game=Game()):
    return game


the_game().play_with_graphics()
