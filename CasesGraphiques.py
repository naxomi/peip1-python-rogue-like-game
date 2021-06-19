import pygame

i = 0


# TODO : Rendre le loading plus rapide en ne loadant qu'une seule fois
def get_image(name):
    global i
    dest = "Images/Elements/"
    sizeFactor = round(16 * 1.25)
    # print(dest+name)
    image = pygame.image.load(dest + name)

    return pygame.transform.scale(image, (sizeFactor, sizeFactor))



def cases_ground(key, floor):
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



def cases_empty(key, floor):
    e = floor.empty
    g = floor.ground
    empty_cells = {
        (g, e, e, e): empty_cells_surfaces[0],
        (e, g, e, e): empty_cells_surfaces[1],
        (g, g, e, e): empty_cells_surfaces[2],

        (g, e, g, e): empty_cells_surfaces[3],
        (g, e, e, g): empty_cells_surfaces[4],

        (e, g, g, e): empty_cells_surfaces[5],
        (e, g, e, g): empty_cells_surfaces[6],

        (g, g, g, e): empty_cells_surfaces[7],
        (g, g, e, g): empty_cells_surfaces[8],

        (e, e, e, g): empty_cells_surfaces[9],
        (e, e, g, e): empty_cells_surfaces[10],
        (e, e, g, g): empty_cells_surfaces[11],
        (g, e, g, g): empty_cells_surfaces[12],

        (e, g, g, g): empty_cells_surfaces[13],
        (g, g, g, g): empty_cells_surfaces[14]
    }
    if key not in empty_cells:
        return False
    return empty_cells[key]


def cases_empty_vertex(key, floor):
    e = floor.empty
    g = floor.ground
    cells_empty_vertex = {
        0: empty_vertex_cells_surfaces[0],
        (e, e, e, e): empty_vertex_cells_surfaces[1],

        (e, e, e, g): empty_vertex_cells_surfaces[2],
        (e, e, g, e): empty_vertex_cells_surfaces[3],
        (e, g, e, e): empty_vertex_cells_surfaces[4],
        (g, e, e, e): empty_vertex_cells_surfaces[5],

        (g, e, g, e, e, g, g, g): empty_vertex_cells_surfaces[6],
        (e, e, g, e, e, g, g, g): empty_vertex_cells_surfaces[7],
        (g, e, e, e, e, g, g, g): empty_vertex_cells_surfaces[8],
        (g, e, g, e, e, e, e, e): empty_vertex_cells_surfaces[9],

        (g, e, g, g, e, g, e, g): empty_vertex_cells_surfaces[10],
        (g, e, g, g, e, g, e, e): empty_vertex_cells_surfaces[11],
        (g, e, e, g, e, g, e, g): empty_vertex_cells_surfaces[12],
        (e, e, g, e, e, e, e, g): empty_vertex_cells_surfaces[13],

        (g, e, g, e, g, g, e, g): empty_vertex_cells_surfaces[14],
        (g, e, g, e, g, e, e, g): empty_vertex_cells_surfaces[15],
        (e, e, g, e, g, g, e, g): empty_vertex_cells_surfaces[16],
        (g, e, e, e, e, g, e, e): empty_vertex_cells_surfaces[17],

        (g, g, g, e, e, g, e, g): empty_vertex_cells_surfaces[18],
        (g, g, g, e, e, e, e, g): empty_vertex_cells_surfaces[19],
        (g, g, g, e, e, g, e, e): empty_vertex_cells_surfaces[20],
        (e, e, e, e, e, g, e, g): empty_vertex_cells_surfaces[21],

        (g, e, g, e, e, g, e, g): empty_vertex_cells_surfaces[22],
        (g, e, e, e, e, g, e, g): empty_vertex_cells_surfaces[23],
        (e, e, g, e, e, g, e, g): empty_vertex_cells_surfaces[24],
        (g, e, g, e, e, e, e, g): empty_vertex_cells_surfaces[25],
        (g, e, g, e, e, g, e, e): empty_vertex_cells_surfaces[26],

        (g, e, e, e, e, e, e, g): empty_vertex_cells_surfaces[27],
        (e, e, g, e, e, g, e, e): empty_vertex_cells_surfaces[28]
    }
    if key not in cells_empty_vertex:
        return False

    return cells_empty_vertex[key]


def generate_graphic_map(floor):
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
                up = floor.get_without_coord(x, y - 1)
            except IndexError:
                up = e

            try:
                down = floor.get_without_coord(x, y + 1)
            except IndexError:
                down = e

            try:
                left = floor.get_without_coord(x - 1, y)
            except IndexError:
                left = e

            try:
                right = floor.get_without_coord(x + 1, y)
            except IndexError:
                right = e

            if elem == g:
                floor.graphicMap[y][x] = [cases_ground((up, down, left, right), floor), False]

            else:

                try:
                    up_left = floor.get_without_coord(x - 1, y - 1, )
                except IndexError:
                    up_left = e

                try:
                    up_right = floor.get_without_coord(x + 1, y - 1)
                except IndexError:
                    up_right = e

                try:
                    down_left = floor.get_without_coord(x - 1, y + 1)
                except IndexError:
                    down_left = e

                try:
                    down_right = floor.get_without_coord(x + 1, y + 1)
                except IndexError:
                    down_right = e

                cells_around = (up_left, up, up_right, left, right, down_left, down, down_right)

                if cases_empty_vertex(cells_around, floor):
                    floor.graphicMap[y][x] = [cases_empty_vertex(cells_around, floor), False]

                elif cases_empty((up, down, left, right), floor):
                    floor.graphicMap[y][x] = [cases_empty((up, down, left, right), floor), False]

                elif cases_empty_vertex((up_left, up_right, down_right, down_left), floor):
                    floor.graphicMap[y][x] = [cases_empty_vertex((up_left, up_right, down_right, down_left), floor),
                                              False]

                else:
                    floor.graphicMap[y][x] = [cases_empty_vertex(0, floor), False]


def get_hero_image(key):
    return [get_image("HeroCostumes/" + key + "/row-" + str(j) + "-col-" + str(i) + ".png") for j in range(1, 5) for i
            in range(1, 5)]


def get_monster_image(key):
    if key != "Hero":
        return [get_image("Monsters/" + key + "-" + str(i) + ".png") for i in range(2)]


def get_item_image(key):
    return get_image("Items/" + key + ".png")


def get_room_object_image(key):
    dest = "Images/Elements/RoomObjects/"
    size_factor = round(16 * 1.25)
    image = pygame.image.load(dest + key + ".png")
    x = image.get_width() * size_factor / 16
    y = image.get_height() * size_factor / 16
    return pygame.transform.scale(image, (int(x), int(y)))
