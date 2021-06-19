import pygame


def getImage(name):
    dest = "Images/Elements/"
    sizeFactor = round(16 * 1.25)
    # print(dest+name)
    image = pygame.image.load(dest + name)

    return pygame.transform.scale(image, (sizeFactor, sizeFactor))


def casesGround(key, floor):
    e = floor.empty
    g = floor.ground
    cases_ground = {
        (e, g, e, g): getImage("Background/FloorTopLeft.png"),
        (e, g, g, g): getImage("Background/FloorTop.png"),
        (e, g, g, e): getImage("Background/FloorTopRight.png"),

        (g, g, e, g): getImage("Background/FloorLeft.png"),
        (g, g, g, g): getImage("Background/Floor.png"),
        (g, g, g, e): getImage("Background/FloorRight.png"),

        (g, e, e, g): getImage("Background/FloorBotLeft.png"),
        (g, e, g, g): getImage("Background/FloorBot.png"),
        (g, e, g, e): getImage("Background/FloorBotRight.png"),

        (g, g, e, e): getImage("Background/FloorCorridorVert.png"),
        (e, e, g, g): getImage("Background/FloorCorridorHoriz.png")
    }
    if key not in cases_ground:
        return False
    return cases_ground[key]


def casesEmpty(key, floor):
    e = floor.empty
    g = floor.ground
    cases_empty = {
        (g, e, e, e): getImage("Background/WallHoriz.png"),
        (e, g, e, e): getImage("Background/WallHoriz.png"),
        (g, g, e, e): getImage("Background/WallHoriz.png"),

        (g, e, g, e): getImage("Background/WallTopLeft.png"),
        (g, e, e, g): getImage("Background/WallTopRight.png"),

        (e, g, g, e): getImage("Background/WallBotLeft.png"),
        (e, g, e, g): getImage("Background/WallBotRight.png"),

        (g, g, g, e): getImage("Background/WallBotLeftUniq.png"),
        (g, g, e, g): getImage("Background/WallBotRightUniq.png"),

        (e, e, e, g): getImage("Background/WallVert.png"),
        (e, e, g, e): getImage("Background/WallVert.png"),
        (e, e, g, g): getImage("Background/WallVert.png"),
        (g, e, g, g): getImage("Background/WallVert.png"),

        (e, g, g, g): getImage("Background/WallDoubleTop.png"),
        (g, g, g, g): getImage("Background/WallDoubleTop.png")
    }
    if key not in cases_empty:
        return False
    return cases_empty[key]


def casesEmptyVertex(key, floor):
    e = floor.empty
    g = floor.ground
    cases_empty_vertex = {
        0: getImage("Background/PitWater.png"),
        (e, e, e, e): getImage("Background/Void.png"),

        (e, e, e, g): getImage("Background/WallTopRight.png"),
        (e, e, g, e): getImage("Background/WallTopLeft.png"),
        (e, g, e, e): getImage("Background/WallBotLeft.png"),
        (g, e, e, e): getImage("Background/WallBotRight.png"),

        (g, e, g, e, e, g, g, g): getImage("Background/WallTripleBot.png"),
        (e, e, g, e, e, g, g, g): getImage("Background/WallTripleBot.png"),
        (g, e, e, e, e, g, g, g): getImage("Background/WallTripleBot.png"),
        (g, e, g, e, e, e, e, e): getImage("Background/WallTripleBot.png"),

        (g, e, g, g, e, g, e, g): getImage("Background/WallTripleLeft.png"),
        (g, e, g, g, e, g, e, e): getImage("Background/WallTripleLeft.png"),
        (g, e, e, g, e, g, e, g): getImage("Background/WallTripleLeft.png"),
        (e, e, g, e, e, e, e, g): getImage("Background/WallTripleLeft.png"),

        (g, e, g, e, g, g, e, g): getImage("Background/WallTripleRight.png"),
        (g, e, g, e, g, e, e, g): getImage("Background/WallTripleRight.png"),
        (e, e, g, e, g, g, e, g): getImage("Background/WallTripleRight.png"),
        (g, e, e, e, e, g, e, e): getImage("Background/WallTripleRight.png"),

        (g, g, g, e, e, g, e, g): getImage("Background/WallTripleTop.png"),
        (g, g, g, e, e, e, e, g): getImage("Background/WallTripleTop.png"),
        (g, g, g, e, e, g, e, e): getImage("Background/WallTripleTop.png"),
        (e, e, e, e, e, g, e, g): getImage("Background/WallTripleTop.png"),

        (g, e, g, e, e, g, e, g): getImage("Background/WallQuadruple.png"),
        (g, e, e, e, e, g, e, g): getImage("Background/WallQuadruple.png"),
        (e, e, g, e, e, g, e, g): getImage("Background/WallQuadruple.png"),
        (g, e, g, e, e, e, e, g): getImage("Background/WallQuadruple.png"),
        (g, e, g, e, e, g, e, e): getImage("Background/WallQuadruple.png"),

        (g, e, e, e, e, e, e, g): getImage("Background/WallQuadruple.png"),
        (e, e, g, e, e, g, e, e): getImage("Background/WallQuadruple.png")
    }
    if key not in cases_empty_vertex:
        return False

    return cases_empty_vertex[key]


def generateGraphicMap(floor):
    m = floor._mat
    e = floor.empty
    g = floor.ground

    if not floor.graphicMap:
        for y in range(len(m) + 1):
            floor.graphicMap.append([[None, False]] * (len(m) + 1))

    for y in range(len(floor.graphicMap)):
        for x in range(len(floor.graphicMap[y])):

            try:
                elem = floor.get_without_coord(x, y)
            except IndexError:
                elem = e

            try:
                haut = floor.get_without_coord(x, y - 1)
            except IndexError:
                haut = e

            try:
                bas = floor.get_without_coord(x, y + 1)
            except IndexError:
                bas = e

            try:
                gauche = floor.get_without_coord(x - 1, y)
            except IndexError:
                gauche = e

            try:
                droite = floor.get_without_coord(x + 1, y)
            except IndexError:
                droite = e

            if elem == g:
                floor.graphicMap[y][x] = [casesGround((haut, bas, gauche, droite), floor), False]

            else:

                try:
                    hautgauche = floor.get_without_coord(x - 1, y - 1, )
                except IndexError:
                    hautgauche = e

                try:
                    hautdroite = floor.get_without_coord(x + 1, y - 1)
                except IndexError:
                    hautdroite = e

                try:
                    basgauche = floor.get_without_coord(x - 1, y + 1)
                except IndexError:
                    basgauche = e

                try:
                    basdroite = floor.get_without_coord(x + 1, y + 1)
                except IndexError:
                    basdroite = e

                casesAutour = (hautgauche, haut, hautdroite, gauche, droite, basgauche, bas, basdroite)

                if casesEmptyVertex(casesAutour, floor):
                    floor.graphicMap[y][x] = [casesEmptyVertex(casesAutour, floor), False]

                elif casesEmpty((haut, bas, gauche, droite), floor):
                    floor.graphicMap[y][x] = [casesEmpty((haut, bas, gauche, droite), floor), False]

                elif casesEmptyVertex((hautgauche, hautdroite, basdroite, basgauche), floor):
                    floor.graphicMap[y][x] = [casesEmptyVertex((hautgauche, hautdroite, basdroite, basgauche), floor),
                                              False]

                else:
                    floor.graphicMap[y][x] = [casesEmptyVertex(0, floor), False]


def getHeroImage(key):
    return [getImage("HeroCostumes/" + key + "/row-" + str(j) + "-col-" + str(i) + ".png") for j in range(1, 5) for i
            in range(1, 5)]


def getMonsterImage(key):
    if key != "Hero":
        return [getImage("Monsters/" + key + "-" + str(i) + ".png") for i in range(2)]


def getItemImage(key):
    return getImage("Items/" + key + ".png")


def getRoomObjectImage(key):
    dest = "Images/Elements/RoomObjects/"
    sizeFactor = round(16 * 1.25)
    image = pygame.image.load(dest + key + ".png")
    x = image.get_width() * sizeFactor / 16
    y = image.get_height() * sizeFactor / 16
    return pygame.transform.scale(image, (int(x), int(y)))
