# visualizes a concrete map of the form laid out in concrete_map.py
import collections #defaultdict
from concrete_map import *
from PIL import Image

#TODO: use path to find the files?
def load_map_tiles(map_dir):
    i0w  = Image.open(map_dir + "/0wall.png")
    i1w  = Image.open(map_dir + "/1wall.png")
    i2w  = Image.open(map_dir + "/2wall.png")
    i2wp = Image.open(map_dir + "/2wallpipe.png")
    i3w  = Image.open(map_dir + "/3wall.png")
    i4w  = Image.open(map_dir + "/4wall.png")
    ba   = Image.open(map_dir + "/blank_alpha.png")
    ia   = Image.open(map_dir + "/item_alpha.png")
    ea   = Image.open(map_dir + "/is_elevator.png")
    et   = Image.open(map_dir + "/elevator.png")
    wall_dict = {"0w" : i0w,
                 "1w" : i1w,
                 "2w" : i2w,
                 "2wp": i2wp,
                 "3w" : i3w,
                 "4w" : i4w,
                 "et" : et
                }
    return wall_dict, ba, ia, ea

def is_below(xy1, xy2):
    """is xy2 directly below xy1?"""
    return xy2 == xy1.down()

def is_left(xy1, xy2):
    return xy2 == xy1.left()

def is_right(xy1, xy2):
    return xy2 == xy1.right()

def is_above(xy1, xy2):
    return xy2 == xy1.up()

def has(wall_list, f, xy):
    """does wall_list have a wall satisfying property f?"""
    return len([w for w in wall_list if f(xy, w)]) > 0

def find_image(walls, xy):
    """returns which image to use, and how to rotate it"""
    nwalls = len(walls)
    # unoptimized spaghetti code
    if nwalls == 0:
        return "0w", 0
    elif nwalls == 1:
        if has(walls, is_left, xy): 
            return "1w", 0
        if has(walls, is_above, xy):
            return "1w", 270
        if has(walls, is_right, xy):
            return "1w", 180
        if has(walls, is_below, xy):
            return "1w", 90
    elif nwalls == 2:
        if has(walls, is_below, xy) and has(walls, is_above, xy):
            return "2wp", 90
        if has(walls, is_left, xy) and has(walls, is_right, xy):
            return "2wp", 0
        if has(walls, is_left, xy) and has(walls, is_above, xy):
            return "2w", 0
        if has(walls, is_above, xy) and has(walls, is_right, xy):
            return "2w", 270
        if has(walls, is_right, xy) and has(walls, is_below, xy):
            return "2w", 180
        if has(walls, is_below, xy) and has(walls, is_left, xy):
            return "2w", 90
    elif nwalls == 3:
        if not has(walls, is_right, xy):
            return "3w", 0
        if not has(walls, is_below, xy):
            return "3w", 270
        if not has(walls, is_left, xy):
            return "3w", 180
        if not has(walls, is_above, xy):
            return "3w", 90
    elif nwalls == 4:
        return "4w", 0
    assert False, "no matching walls! " + str(walls)
       
def map_viz(rcmap, filename, map_dir):
    mrange, mins = map_range(rcmap)
    map_image = Image.new("RGBA", ((mrange.x+1)*16, (mrange.y+1)*16), "black")
    # bind the current region for easy re-use
    wmap, blank, item, elevator = load_map_tiles(map_dir)
    for x in range(mrange.x+1):
        for y in range(mrange.y+1):
            relxy = MCoords(x, y) + mins
            xy = (x,y)
            if relxy in rcmap:
                mtile = rcmap[relxy]
                if mtile.is_e_shaft:
                    image_name, rotation = "et", 0
                else:
                    image_name, rotation = find_image(mtile.walls, relxy)
                image = wmap[image_name]
                imrotate = image.rotate(rotation)
                map_image.paste(imrotate, (x*16,y*16), imrotate)
                if mtile.is_item:
                    map_image.paste(item, (x*16,y*16), item)
                if mtile.is_e_main:
                    map_image.paste(elevator, (x*16,y*16), elevator)
            else:
                # it's a blank
                map_image.paste(blank, (x*16,y*16), blank)
    map_image.save(filename)
    return map_image

def gen_cases(lrep):
    """take a pattern-matching TF line and generate the cases"""
    if len(lrep) == 1:
        if lrep[0] == "T":
            return [[True]]
        elif lrep[0] == "F":
            return [[False]]
        else:
            return [[True], [False]]
    if lrep[0] == "T":
        return map(lambda l: [True] + l[:], gen_cases(lrep[1:]))
    elif lrep[0] == "F":
        return map(lambda l: [False] + l[:], gen_cases(lrep[1:])) #TODO: do I need this copy?
    elif lrep[0] == "_":
        c1 = map(lambda l: [True] + l[:], gen_cases(lrep[1:])) #TODO: do I need this copy?
        c2 = map(lambda l: [False] + l[:], gen_cases(lrep[1:])) #TODO: do I need this copy?
        return c1 + c2
    else:
        assert False, lrep

def tiles_parse(tile_file):
    """Creates a simple boolean pattern matching dictionary.
    out is a dict where key = a tuple of bools specifying what type of tile
    and value = a tuple of (vflip, hflip, tile index) or None if there is no matching tile."""
    out = {}
    f = open(tile_file, "r")
    # first, reverse the readlines so newer things are applied last
    ls = f.readlines()[::-1]
    for line in ls:
        if len(line) == 0:
            continue
        elif line[0] == "#":
            continue
        else:
            line =  line.strip()
            line = line.split()
            if len(line) == 0:
                continue
            if line[-1] == "ERROR":
                val = None
                lrep = line[:-1]
            else:
                val = tuple(line[-3:])
                lrep = line[:-3]
            cases = gen_cases(lrep)
            keys = map(lambda l: tuple(l), cases)
            for k in keys:
                out[k] = val
    return out

def cmap_to_tuples(cmap, tile_mapping):
    """ create an dict of key - xy, value - (hflip, vflip, index) from a cmap for that area"""
    cmap_tuples = {}
    for mc, tile in cmap.items():
        xy = (mc.x, mc.y)
        is_e_arrow = tile.is_e_arrow
        is_e_shaft = tile.is_e_shaft
        is_e_main  = tile.is_e_main
        is_e_up    = tile.is_e_up
        is_save    = tile.is_save
        is_item    = tile.is_item
        l          = mc.left() in tile.walls
        u          = mc.up() in tile.walls
        r          = mc.right() in tile.walls
        d          = mc.down() in tile.walls
        t = (is_e_arrow, is_e_shaft, is_e_main, is_e_up, is_save, is_item, l, u, r, d)
        if tile_mapping[t] is not None:
            cmap_tuples[xy] = tile_mapping[t]
    return cmap_tuples

