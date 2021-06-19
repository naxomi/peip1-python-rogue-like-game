import copy
import math
import random
import CasesGraphiques as CG
import pygame


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


def opp(x):
    return -x + 1


def clearList(liste):
    for i in range(len(liste)):
        for j in range(len(liste)):
            liste[i][j] = None


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

    def __init__(self, name, abbreviation=""):
        self.name = name
        if abbreviation == "":
            abbreviation = name[0]
        self.abbreviation = abbreviation

        self.graphicOutput = None

    def __repr__(self):
        return self.abbreviation

    def description(self):
        """Description of the element"""
        return "<" + self.name + ">"

    def meet(self, hero):
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

        g = theGame()
        ret = self.usage()

        return ret

    @staticmethod
    def monterEtage():
        g = theGame()
        if g.actualFloor + 1 < len(g.floorList):
            g.floor.rm(g.floor.pos(g.hero))

            g.actualFloor += 1
            g.floor = g.gv.floor = g.floorList[g.actualFloor]
            g.addMessage('You are now in stage ' + str(g.actualFloor + 1) + '/' + str(len(g.floorList)))

            stairCoord = g.floor.pos(g._roomObjects['downstair'])
            newCoord = stairCoord.getEmptyCoordAround(g.floor)

            g.floor.put(newCoord, g.hero)
            g.hero.x = newCoord.x
            g.hero.y = newCoord.y
            return True
        return False

    @staticmethod
    def descendreEtage():
        g = theGame()
        if g.actualFloor - 1 >= 0:
            g.floor.rm(g.floor.pos(g.hero))

            g.actualFloor -= 1
            g.floor = g.gv.floor = g.floorList[g.actualFloor]
            g.addMessage('You are now in stage ' + str(g.actualFloor + 1) + '/' + str(len(g.floorList)))

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
            l.append(theGame().randElement(Game.equipments))
        l.append(theGame().randElement(Game._weapons))

        theGame().gv.drawMarchand(l)


class Creature(Element):
    """A creature that occupies the dungeon.
        Is an Element. Has hit points and strength."""

    defaultInventorySize = 10

    def __init__(self, name, hp, abbreviation="", strength=1, xp=1, weaponSlot=None):
        Element.__init__(self, name, abbreviation)
        self.hp = hp
        self.strength = strength
        self.xp = xp

        if weaponSlot != None:
            self.weaponSlot = weaponSlot
        else:
            self.weaponSlot = []

        self._inventory = []
        self._ephemereEffects = {}
        self._constantEffectsToApply = {}
        self._constantEffectsApplied = {}

        # Graphics
        self.graphicOutput = CG.getMonsterImage(self.name)

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
            other.gain_xp(self.xp)
        return True

    def hit(self, other):
        if other.hasWeapon() and other.hasAnHittingWeapon():
            self.hp -= other.currentWeapon().damage
        else:
            self.hp -= other.strength

    def addEffect(self, effect, unique=True):
        """The hero now has a new effect, maybe after using a potion or being attacked"""

        effect.effectFunc(self, effect.value)

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


class Hero(Creature):
    """The hero of the game.
        Is a creature. Has an inventory of elements. """

    defaultInventorySize = 10
    defaultStomachSize = 5
    defaultLevelSize = 25

    defaultHp = 10

    def __init__(self, name="Hero", hp=defaultHp, abbreviation="@", strength=10, level=1, xp=0, gold=0,
                 stomach=defaultStomachSize, weaponSlot=None):
        Creature.__init__(self, name, hp, abbreviation, strength, weaponSlot)

        self.xp = xp
        self.toNextLevel = Hero.defaultLevelSize
        self.level = level

        self.gold = gold
        self.stomach = stomach
        '''
        if weaponSlot == None:
            self.weaponSlot = []
        else:
            self.weaponSlot = weaponSlot
        '''

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
        res += '> Ephemere Effects : ' + str(
            [x.name + " <" + str(self._ephemereEffects[x][0]) + " round(s)>" for x in self._ephemereEffects]) + '\n'
        res += '> Constant Effects : ' + str([x.name for x in self._constantEffectsApplied]) + '\n'
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
                    theGame().addMessage("Wrong value entered.")

    def checkInvSize(self):
        if len(self._inventory) > Hero.defaultInventorySize:
            theGame().addMessage("Inventaire complet.\nVeuillez supprimer un élément.")
            return False
        return True

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
                theGame().addMessage("You have succesfully deleted the item :\n" + str(elem.name))
            else:
                theGame().addMessage("Could not find the item to delete.\nMaybe try with another value")

    def gain_xp(self, creatureXP):

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

        theGame().addMessage("You now have a strength of {0}\nand won {1} gold coins".format(self.strength, self.level))

    def verifyStomach(self):
        if self.stomach == 0:
            self.__dict__["hp"] -= 1

    def applyAllAmulets(self):
        return True

    def buy(self, o):
        if isinstance(o, Equipment):
            if self.checkInvSize():
                if self.gold >= o.price:
                    self.gold -= o.price
                    self.take(o)
                    theGame().addMessage(f'You bought {o.name} for {o.price} gold')
                else:
                    theGame().addMessage(f'Not enough gold. {o.price - self.gold} gold left.')


class Effect(object):
    _effectTypeList = ["instant", "ephemere", "constant"]

    def __init__(self, name="", benefic=True, effectFunc=None, effectType=_effectTypeList[0], duration=1, value=None):
        self.name = name
        self.benefic = benefic
        self.effectFunc = effectFunc
        self.effectType = effectType
        self.value = value

        if self.effectType == "ephemere":
            self.duration = duration

    ### Instant power
    ### Constant power
    ### Ephemere power

    def hunger(hero, foodLost):
        """Remove food from the hero"""
        hero.__dict__["stomach"] -= foodLost

        theGame().addMessage("You now have {0}/{1} food".format(hero.stomach, hero.defaultStomachSize))

    def poison(creature, hpLost):
        """Remove health from the creature"""
        creature.__dict__["hp"] -= hpLost

        if isinstance(creature, Hero):
            theGame().addMessage("You have been poisoned and now have {0} health".format(creature.hp))

    # else:
    #    the_game().addMessage("The creature <{0}> now has {1} health").format(creature.name, creature.hp)

    def heal(creature, hpWon):
        """Heal the creature"""
        creature.__dict__["hp"] += hpWon

        if isinstance(creature, Hero):
            theGame().addMessage("You now have {0} health".format(creature.hp))
        else:
            theGame().addMessage("The creature <{0}> now has {1} health").format(creature.name, creature.hp)

    def teleport(creature, value=None):
        """Teleport the creature"""
        r = theGame().floor.randRoom()
        c = r.rand_coord()
        while not theGame().floor.get(c) == Map.ground:
            c = r.rand_coord()
        theGame().floor.rm(theGame().floor.pos(creature))
        theGame().floor.put(c, creature)

        if isinstance(creature, Hero):
            theGame().addMessage("You have been teleported")
        else:
            theGame().addMessage("The creature <{0}> has been teleported").format(creature.name)

    def feed(hero, foodValue):
        if hero.defaultStomachSize >= hero.stomach + foodValue:
            hero.__dict__["stomach"] += foodValue
        else:
            hero.__dict__["stomach"] += hero.defaultStomachSize - hero.stomach

        theGame().addMessage("You now have {0}/{1} food".format(hero.stomach, hero.defaultStomachSize))

    def giveStrength(creature, strengthPoint):
        """Can be used in potions and items to give strength to the creature"""
        creature.__dict__["strength"] += strengthPoint

    def giveHealth(creature, healthPoint):
        """Give more health to the creature while she has the effect active"""
        creature.__dict__["hp"] += healthPoint

    def giveWeakness(creature, strengthPoint):
        """Remove some strength from the creature"""
        creature.__dict__["strength"] -= strengthPoint


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
        theGame().addMessage("You pick up a " + self.name)
        return True

    def use(self, creature):
        """Uses the piece of equipment. Has effect on the hero according usage.
            Return True if the object is consumed."""
        if self.usage is None:
            theGame().addMessage("The " + self.name + " is not usable")
            return False
        elif isinstance(self, Weapon) and self.weaponType != Weapon._weaponTypeList[0]:
            theGame().addMessage("The " + creature.name + " uses the " + self.name)
            return self.usage(self, creature)

        else:
            theGame().addMessage("The " + creature.name + " uses the " + self.name)
            return self.usage(self, creature)

    '''	
    def isDurabilityValid(self):
        if self.durability == 0:
            return False
        return True
    '''


class Weapon(Equipment):
    """A weapon which can be used by the Hero or the monsters"""

    _weaponTypeList = ["hit", "throw", "projectile"]

    def __init__(self, name, abbreviation="", weaponType=_weaponTypeList[0], usage=None, effectsList=None, damage=1,
                 durability=10, price=2):
        Equipment.__init__(self, name, abbreviation, usage, durability, price=price)
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
        # Same as randEmpty Coord but on top
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
        map.put(self.rand_empty_coord(map), theGame().randEquipment())
        map.put(self.rand_empty_coord(map), theGame().randMonster())


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
        self.generateRooms(7)
        self.reachAllRooms()

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

    def putRoomObjects(self):
        for key in Game._roomObjects:
            if key == "downstair" and self.floorNumber > 0:
                r = random.choice(self._rooms)
                r.specialObjects.append(Game._roomObjects[key])
            if key == "upstair" and self.floorNumber + 1 < theGame().nbFloors:
                r = random.choice(self._rooms)
                r.specialObjects.append(Game._roomObjects[key])

    def randRoom(self):
        """A random room to be put on the map."""
        c1 = Coord(random.randint(0, len(self) - 3), random.randint(0, len(self) - 3))
        c2 = Coord(min(c1.x + random.randint(4, 8), len(self) - 1), min(c1.y + random.randint(4, 8), len(self) - 1))
        return Room(c1, c2)

    def generateRooms(self, n):
        """Generates n random rooms and adds them if non-intersecting."""
        if self.specialRoom is not None:
            self.addRoom(Game._specialRoomsList[self.specialRoom])
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

    def inGraphicMap(self, c):
        return 0 <= c.x < len(self.graphicMap) and 0 <= c.y < len(self.graphicMap)

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
            print('ici:', self._mat[c.y][c.x])
            raise ValueError('Incorrect cell')
        if o in self._elem:
            raise KeyError('Already placed')
        self._mat[c.y][c.x] = o
        self._elem[o] = c

    def get(self, c):
        """Returns the object present on the cell c"""
        try:
            self.checkCoord(c)
        except IndexError:
            return Map.empty
        return self._mat[c.y][c.x]

    def get_without_coord(self, x, y):
        self.checkCoord(Coord(x, y))
        return self._mat[y][x]

    def pos(self, o):
        """Returns the coordinates of an element in the map """
        if o in self._elem:
            self.checkElement(o)
            return self._elem[o]
        else:
            return None

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
                if isinstance(e, Hero):
                    self.hero.x, self.hero.y = dest.x, dest.y
            elif isinstance(self.get(dest), RoomObject) and self.get(dest).meet(e):
                pass
            # self.rm(self.pos(self.hero))
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
        d = c1
        wayFinale = Coord(0, 0)
        for i in range(-1, 2):
            for j in range(-1, 2):
                way = Coord(i, j)
                inMap = 0 <= c1.x + way.x < len(self._mat) and 0 <= c1.y + way.y < len(self._mat)
                if inMap and (c1 + way).distance(c2) < (c1 + wayFinale).distance(c2) and self.get(
                        c1 + way) == self.ground:
                    wayFinale = way
        return wayFinale

    def moveAllMonsters(self):
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
        theGame().gv.updateBrouillard(self)

    def applyEffectsToAllMonsters(self):

        coordToDel = []
        for e in self._elem:
            if isinstance(e, Creature) and not isinstance(e, Hero):
                e.applyAllEffects()

                if e.__dict__["hp"] <= 0:
                    coordToDel.append(self.pos(e))

        for coord in coordToDel:
            self.rm(coord)


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

        self.qwerty = True

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
            image = CG.getImage("Animations\\explosion-" + str(i) + ".png")
            self.explosion.append(pygame.transform.scale(image, (40, 40)))

        self.hearts = []
        for i in range(5):
            image1 = CG.getImage("GUI\\heart" + str(i) + "-0.png")
            image2 = CG.getImage("GUI\\heart" + str(i) + "-1.png")
            self.hearts.append([image1, image2])

        self.blackhearts = []
        for i in range(5):
            image1 = CG.getImage("GUI\\blackheart" + str(i) + "-0.png")
            image2 = CG.getImage("GUI\\blackheart" + str(i) + "-1.png")
            self.blackhearts.append([image1, image2])

        self.xpbar = []
        for i in range(5):
            self.xpbar.append(CG.getImage("GUI\\xp" + str(i) + ".png"))

        self.xpbord = []
        for i in range(3):
            self.xpbord.append(CG.getImage("GUI\\bordexp" + str(i) + ".png"))

        self.blockSpace = pygame.transform.scale(CG.getImage("GUI\\blockSpace.png"), (32, 32))
        self.brouillard = CG.getImage("Background\\Brouillard.png")

        self.food = [CG.getImage("GUI\\food0.png"), CG.getImage("GUI\\food1.png")]
        self.dollar = CG.getImage("GUI\\dollar.png")
        self.arrow = CG.getImage("GUI\\arrow.png")

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
        if len(self.hero.weaponSlot) != 0:
            self.screen.blit(self.hero.weaponSlot[0].graphicOutput[1],
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

    def drawMessage(self, time):
        # Draw Message self.screen
        self.screen.fill((20, 12, 28), (
        (self.width / 2) * (1 + 1 / 8), self.height * 3 / 4, (self.width / 2) * 6 / 8, self.height / 5))
        b = 5
        self.screen.fill((140, 140, 150), (
        (self.width / 2) * (1 + 1 / 8) + b, self.height * 3 / 4 + b, (self.width / 2) * 6 / 8 - 2 * b,
        self.height / 5 - 2 * b))

        newmsg = theGame().readMessages()
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
                    '''
                    # Diagonals
                    if event.key == pygame.K_q:
                            self.hero.moovingUDLR[0] = keydownBool
                            self.hero.moovingUDLR[2] = keydownBool
                    elif event.key == pygame.K_e:
                            self.hero.moovingUDLR[0] = keydownBool
                            self.hero.moovingUDLR[3] = keydownBool
                    elif event.key == pygame.K_c:
                            self.hero.moovingUDLR[1] = keydownBool
                            self.hero.moovingUDLR[3] = keydownBool
                    elif event.key == pygame.K_z:
                            self.hero.moovingUDLR[1] = keydownBool
                            self.hero.moovingUDLR[2] = keydownBool
                    '''
                else:
                    if event.key == pygame.K_z:
                        self.hero.moovingUDLR[0] = keydownBool
                    elif event.key == pygame.K_x:
                        self.hero.moovingUDLR[1] = keydownBool
                    elif event.key == pygame.K_a:
                        self.hero.moovingUDLR[2] = keydownBool
                    elif event.key == pygame.K_d:
                        self.hero.moovingUDLR[3] = keydownBool
                    '''
                    # Diagonals
                    if event.key == pygame.K_a:
                            self.hero.moovingUDLR[0] = keydownBool
                            self.hero.moovingUDLR[2] = keydownBool
                    elif event.key == pygame.K_e:
                            self.hero.moovingUDLR[0] = keydownBool
                            self.hero.moovingUDLR[3] = keydownBool
                    elif event.key == pygame.K_c:
                            self.hero.moovingUDLR[1] = keydownBool
                            self.hero.moovingUDLR[3] = keydownBool
                    elif event.key == pygame.K_w:
                            self.hero.moovingUDLR[1] = keydownBool
                            self.hero.moovingUDLR[2] = keydownBool
                    '''
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
            Game._actions["b"]
            self.inventoryOn = False

        elif event.key == pygame.K_i:
            self.inventoryOn = False

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
        cle = 'Images\\musiques\\'
        self._songs = self._songs[1:] + [self._songs[0]]  # move current song to the back of the list
        pygame.mixer.music.load(cle + self._songs[0])
        pygame.mixer.music.play()
        print(self._songs[0])


class Game(object):
    """ Class representing game state """

    """ available equipments """
    equipments = {0: [Equipment("gold", "o"), \
                      Equipment("healing potion", "!", usage=lambda self, hero: hero.addEffect(
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
                  1: [Equipment("teleport potion", "!", usage=lambda self, hero: hero.addEffect(
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
    """ available monsters """
    monsters = {0: [Creature("Goblin", hp=4, strength=1, xp=4), \
                    Creature("Bat", hp=2, abbreviation="W", strength=1, xp=2), \
                    Creature("BabyDemon", hp=2, strength=2, xp=4)], \
                1: [Creature("Ork", hp=6, strength=2, xp=10), \
                    Creature("Blob", hp=10, xp=8), \
                    Creature("Angel", hp=10, strength=1, xp=4)], \
                3: [Creature("Poisonous spider", hp=5, xp=10, strength=0, abbreviation="&", powers_list=[[PoisonEffect, 2, 1]])],
                5: [Creature("Dragon", hp=20, strength=3, xp=50)],
                20: [Creature("Death", hp=50, strength=3, xp=100, abbreviation='ñ')] \
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
                # 'i': lambda h: the_game().addMessage(h.fullDescription()), \
                'k': lambda h: h.__setattr__('hp', 0), \
                # 'u': lambda h: h.use(the_game().select(h._inventory)), \
                'u': lambda h: h.use(theGame().gv.selectFromInventory(Equipment)), \
                ' ': lambda h: None, \
                'h': lambda hero: theGame().addMessage("Actions disponibles : " + str(list(Game._actions.keys()))), \
                't': lambda hero: hero.deleteItem(
                    theGame().gv.selectFromInventory(Equipment) if len(hero._inventory) > 0 else False), \
                'b': lambda hero: hero.equipWeapon(theGame().gv.selectFromInventory(Weapon)) if any(
                    isinstance(elem, Weapon) for elem in hero._inventory) else theGame().addMessage(
                    "You don't have any weapon in your inventory"), \
                'n': lambda hero: hero.removeCurrentWeapon(), \
 \
                # 's': saveGame(the_game()), \
                }

    """ available weapons """
    _weapons = {
        0: [Weapon("Basic Sword", "†", weaponType=Weapon._weaponTypeList[0], usage=lambda self, hero: Weapon.hit)], \
        1: [Weapon("Shuriken", "*", weaponType=Weapon._weaponTypeList[0], usage=lambda self, hero: Weapon.hit)], \
        # 2: [], \
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
        self._message = []
        if hero == None:
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

    def buildFloor(self):
        """Creates maps for the floors."""

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

    def addMessage(self, msg):
        """Adds a message in the message list."""
        if '\n' in msg:
            l = msg.split('\n')
            for m in l:
                self._message.append(m)

        else:
            self._message.append(msg)

    def readMessages(self):
        """Returns the message list and clears it."""
        renders = []
        for m in self._message:
            renders.append(self.gv.gameFont.render(m, True, (0, 0, 0)))

        self._message.clear()
        return renders.copy()

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

        if c.isdigit() and int(c) in range(len(l)) and len(l) != 0:
            return l[int(c)]
        elif len(l) == 0:
            print("You don't have any item in your inventory.")

    def selectItemToDel(self, l):
        print("Choose an item to delete> " + str([str(l.index(e)) + ": " + e.name for e in l]))

        c = getch()

        if c.isdigit() and int(c) in range(len(l)) and len(l) != 0:
            return l[int(c)]
        elif len(l) == 0:
            print("You don't have any item in your inventory.")

    def selectWeapon(self, l):

        listWeapon = [e for e in l if isinstance(e, Weapon)]

        print("Choose a weapon> " + str([str(listWeapon.index(e)) + ": " + e.name for e in listWeapon]))

        c = getch()

        if c.isdigit() and int(c) in range(len(listWeapon)) and len(listWeapon) != 0:
            return listWeapon[int(c)]

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

    def playWithGraphics(self):

        print("\n--- Initialiting Graphics ---")
        print("Loading ...")

        self.buildFloor()
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

                self.hero.checkInventorySize()

                if self.gv.newRound:
                    self.gv.newRound = False
                    self.numberOfRound += 1
                    self.applyEffectsBool = True

                    # self.gv.updateBrouillard()
                    self.floor.moveAllMonsters()

                    if self.numberOfRound % 20 == 0 and self.hero.__dict__["stomach"] > 0:
                        self.hero.__dict__["stomach"] -= 1
                    self.hero.verifyStomach()

                if self.applyEffectsBool:
                    # TODO : Replace by new way of doing it
                    self.hero.applyAllEffects()
                    self.floor.applyEffectsToAllMonsters()
                    self.applyEffectsBool = False

                # Messages
                self.gv.drawMessage(200)

                self.gv.drawGameScreen()

            pygame.display.update()
        # running = False

        pygame.quit()


def theGame(game=Game()):
    """Game singleton"""
    return game


theGame().playWithGraphics()
# print