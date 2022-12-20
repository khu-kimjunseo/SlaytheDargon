import cocos.tiles
from cocos.director import director

move_map_image = 'image/Movemap.tmx'
battle_map_image = 'battlemap/Battlemap.tmx'
move_map = 'map1'
battle_map = 'map1'

class Scenario(object):
    def __init__(self, map_image, tmx_map):
        self.map = cocos.tiles.load(map_image)
        self.bg = self.map[tmx_map]
        self._actions = None

    def get_background(self):
        self.bg.set_view(0, 0, self.bg.px_width, self.bg.px_height)
        return self.bg

    def get_map_size(self):
        w = self.bg.px_width
        h = self.bg.px_height
        return w, h


def get_move_scenario():
    sc = Scenario(move_map_image, move_map)
    return sc

def get_battle_scenario():
    sc = Scenario(battle_map_image, battle_map)
    return sc