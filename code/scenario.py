import cocos.tiles
import cocos.actions as ac

map_image = 'image/untitled.tmx'
map_layer = 'map0'

class Scenario(object):
    def __init__(self, tmx_map):
        self.tmx_map = tmx_map
        self._actions = None

    def get_background(self):
        tmx_map = cocos.tiles.load(map_image)
        bg = tmx_map[self.tmx_map]
        bg.set_view(0, 0, bg.px_width, bg.px_height)
        return bg


def get_scenario():
    sc = Scenario(map_layer)
    return sc
