import pygame


def get_image(name):
    dest = "Images/Elements/"
    size_factor = round(16 * 1.25)
    # print(dest+name)
    image = pygame.image.load(dest + name)

    return pygame.transform.scale(image, (size_factor, size_factor))


ground_cell_paths = ["Background/FloorTopLeft.png",
                     "Background/FloorTop.png",
                     "Background/FloorTopRight.png",

                     "Background/FloorLeft.png",
                     "Background/Floor.png",
                     "Background/FloorRight.png",

                     "Background/FloorBotLeft.png",
                     "Background/FloorBot.png",
                     "Background/FloorBotRight.png",

                     "Background/FloorCorridorVert.png",
                     "Background/FloorCorridorHoriz.png"]
ground_cell_surfaces = [get_image(img_path) for img_path in ground_cell_paths]


def cases_ground(key, floor):
    e = floor.empty
    g = floor.ground
    ground_cells = {
        (e, g, e, g): ground_cell_surfaces[0],
        (e, g, g, g): ground_cell_surfaces[1],
        (e, g, g, e): ground_cell_surfaces[2],

        (g, g, e, g): ground_cell_surfaces[3],
        (g, g, g, g): ground_cell_surfaces[4],
        (g, g, g, e): ground_cell_surfaces[5],

        (g, e, e, g): ground_cell_surfaces[6],
        (g, e, g, g): ground_cell_surfaces[7],
        (g, e, g, e): ground_cell_surfaces[8],

        (g, g, e, e): ground_cell_surfaces[9],
        (e, e, g, g): ground_cell_surfaces[10]
    }
    if key not in ground_cells:
        return False
    return ground_cells[key]


empty_cells_paths = [
    "Background/WallHoriz.png",
    "Background/WallHoriz.png",
    "Background/WallHoriz.png",

    "Background/WallTopLeft.png",
    "Background/WallTopRight.png",

    "Background/WallBotLeft.png",
    "Background/WallBotRight.png",

    "Background/WallBotLeftUniq.png",
    "Background/WallBotRightUniq.png",

    "Background/WallVert.png",
    "Background/WallVert.png",
    "Background/WallVert.png",
    "Background/WallVert.png",

    "Background/WallDoubleTop.png",
    "Background/WallDoubleTop.png"
]
empty_cells_surfaces = [get_image(img_path) for img_path in empty_cells_paths]


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


empty_vertex_cells_paths = [
    "Background/PitWater.png",
    "Background/Void.png",

    "Background/WallTopRight.png",
    "Background/WallTopLeft.png",
    "Background/WallBotLeft.png",
    "Background/WallBotRight.png",

    "Background/WallTripleBot.png",
    "Background/WallTripleBot.png",
    "Background/WallTripleBot.png",
    "Background/WallTripleBot.png",

    "Background/WallTripleLeft.png",
    "Background/WallTripleLeft.png",
    "Background/WallTripleLeft.png",
    "Background/WallTripleLeft.png",

    "Background/WallTripleRight.png",
    "Background/WallTripleRight.png",
    "Background/WallTripleRight.png",
    "Background/WallTripleRight.png",

    "Background/WallTripleTop.png",
    "Background/WallTripleTop.png",
    "Background/WallTripleTop.png",
    "Background/WallTripleTop.png",

    "Background/WallQuadruple.png",
    "Background/WallQuadruple.png",
    "Background/WallQuadruple.png",
    "Background/WallQuadruple.png",
    "Background/WallQuadruple.png",

    "Background/WallQuadruple.png",
    "Background/WallQuadruple.png"

]

empty_vertex_cells_surfaces = [get_image(img_path) for img_path in empty_vertex_cells_paths]


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

    if not floor.graphic_map:
        for y in range(len(m) + 1):
            floor.graphic_map.append([[None, False]] * (len(m) + 1))

    for y in range(len(floor.graphic_map)):
        for x in range(len(floor.graphic_map[y])):

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
                floor.graphic_map[y][x] = [cases_ground((up, down, left, right), floor), False]

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
                    floor.graphic_map[y][x] = [cases_empty_vertex(cells_around, floor), False]

                elif cases_empty((up, down, left, right), floor):
                    floor.graphic_map[y][x] = [cases_empty((up, down, left, right), floor), False]

                elif cases_empty_vertex((up_left, up_right, down_right, down_left), floor):
                    floor.graphic_map[y][x] = [cases_empty_vertex((up_left, up_right, down_right, down_left), floor),
                                               False]

                else:
                    floor.graphic_map[y][x] = [cases_empty_vertex(0, floor), False]


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
