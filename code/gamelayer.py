import random

from cocos.director import director
from cocos.scenes.transitions import SplitColsTransition, FadeTransition
import cocos.layer
import cocos.scene
import cocos.text
import cocos.actions as ac
import cocos.collision_model as cm

import actors
import mainmenu
from scenario import get_scenario

player_img = 'assets/tank.png'

class MoveLayer(cocos.layer.Layer):
    is_event_handler = True

    def on_key_press(self, k, _):
        actors.Player.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        actors.Player.KEYS_PRESSED[k] = 0

    def __init__(self, hud, scenario):
        super(MoveLayer, self).__init__()
        self.hud = hud
        w, h = director.get_window_size()
        self.width = w
        self.height = h
        self.player = actors.Player(player_img, w * 0.5, 50)
        self.add(self.player)
        cell_size = 32
        self.coll_man = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        self.schedule(self.game_loop)

    def game_loop(self, elapsed):
        self.player.update(elapsed)

class Move_HUD(cocos.layer.Layer):
    def __init__(self):
        super(Move_HUD, self).__init__()
        w, h = director.get_window_size()
        self.score_text = self._create_text(60, h-40)
        self.score_points = self._create_text(w-60, h-40)

    def _create_text(self, x, y):
        text = cocos.text.Label(font_size=18, font_name='Oswald',
                                anchor_x='center', anchor_y='center')
        text.position = (x, y)
        self.add(text)
        return text

    def update_score(self, score):
        self.score_text.element.text = 'Score: %s' % score

    def update_points(self, points):
        self.score_points.element.text = 'Points: %s' % points

def new_game():
    scenario = get_scenario()
    background = scenario.get_background()
    hud = HUD()
    game_layer = MoveLayer(hud, scenario)
    return cocos.scene.Scene(background, game_layer, hud)


def game_over():
    w, h = director.get_window_size()
    layer = cocos.layer.Layer()
    text = cocos.text.Label('Game Over', position=(w*0.5, h*0.5),
                            font_name='Oswald', font_size=72,
                            anchor_x='center', anchor_y='center')
    layer.add(text)
    scene = cocos.scene.Scene(layer)
    new_scene = FadeTransition(mainmenu.new_menu())
    func = lambda: director.replace(new_scene)
    scene.do(ac.Delay(3) + ac.CallFunc(func))
    return scene

class BattleLayer(cocos.layer.Layer):
    is_event_handler = True