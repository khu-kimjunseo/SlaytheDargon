import random

from pyglet.window import key

from cocos.director import director
from cocos.scenes.transitions import SplitColsTransition, FadeTransition
import cocos.layer
import cocos.scene
import cocos.text
import cocos.actions as ac
import cocos.collision_model as cm
from cocos.scenes.transitions import FadeTRTransition

import actors
import mainmenu
import scenario as sc

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
        self.enemy0 = actors.Enemy(player_img, 300, 300)
        self.add(self.enemy0)

        cell_size = 32
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        self.schedule(self.game_loop)

    def game_loop(self, elapsed):
        self.player.update(elapsed)

        self.collman.clear()
        for _, node in self.children:
            self.collman.add(node)
            if not self.collman.knows(node):
                self.remove(node)
        for _, node in self.children:
            if isinstance(node, actors.Player):
                enemy = self.collide(node)
                if enemy is not None:
                    director.push(FadeTRTransition(new_battle(node, enemy), duration=2))
        
        for _, node in self.children:
            if isinstance(node, actors.Enemy):
                if node.hp == 0:
                    if node.is_running:
                        self.remove(node)

    def collide(self, node):
        if node is not None:
            for other in self.collman.iter_colliding(node):
                node.collide(other)
                return other
        return None
        
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
    scenario = sc.get_move_scenario()
    background = scenario.get_background()
    hud = Move_HUD()
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

    def on_key_press(self, k, _):
        if k == key.Q:
            self.enemy.hp = 0
            # self.enemy.kill()
            self.player.position = self.return_pos
            director.pop()
    
    def on_mouse_press(self, x, y, buttons, mod):
        cards = self.collman.objs_touching_point(x, y)
        if len(cards):
            card = next(iter(cards))
            card.kill()

    def __init__(self, hud, scenario, player, enemy):
        super(BattleLayer, self).__init__()
        self.hud = hud
        w, h = director.get_window_size()
        self.width = w
        self.height = h
        self.player = player
        self.add(self.player)
        self.enemy = enemy
        self.add(self.enemy)

        self.return_pos = self.player.position

        self.player.position = (200, 0.75*self.height)
        self.player.cshape.center = (200, 0.75*self.height)
        self.enemy.position = (self.width-200, 0.75*self.height)
        self.enemy.cshape.center = (self.width-200, 0.75*self.height)
        self.card_i = 0
        random.shuffle(self.player.decks)
        
        cell_size = 32
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        self.schedule(self.game_loop)

        self.create_cards()

    def game_loop(self, elapsed):
        self.player.update(elapsed)

    def create_cards(self):
        cards = []
        for i in range(4):
            if self.card_i >= len(self.player.decks):
                random.shuffle(self.player.decks)
                self.card_i = 0
            cards.append(self.player.decks[self.card_i])
            cards[i].position = (0.5 * self.width + 100*(i-2), 0)
            cards[i].cshape.center = (0.5 * self.width + 100*(i-2), 0)
            self.add(cards[i])
            self.collman.add(cards[i])
            self.card_i += 1
            

def new_battle(player, enemy):
    scenario = sc.get_battle_scenario()
    background = scenario.get_background()
    hud = Move_HUD()
    game_layer = BattleLayer(hud, scenario, player, enemy)
    return cocos.scene.Scene(background, game_layer, hud)