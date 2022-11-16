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
                if node.hp <= 0:
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
    
    def on_mouse_press(self, x, y, buttons, mod):
        cards = self.collman.objs_touching_point(x, y)
        if len(cards):
            card = next(iter(cards))
            self.player.cost -= 1
            card.activate()
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

        self.movelayer = director.scene_stack[-1]

        self.return_pos = self.player.position

        self.player.position = (200, 0.75*self.height)
        self.player.cshape.center = (200, 0.75*self.height)
        self.enemy.position = (self.width-200, 0.75*self.height)
        self.enemy.cshape.center = (self.width-200, 0.75*self.height)
        self.card_i = 0
        random.shuffle(self.player.decks)
        
        self.attack()
        self.defense()
        self.enemy_attack()

        cell_size = 32
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        self.schedule(self.game_loop)

        self.create_cards()

    def attack(self, damage=0):
        self.enemy.hp -= damage
        self.hud.update_enemy_hp(self.enemy.hp)
        self.hud.update_cost(self.player.cost)

    def defense(self, armor=0):
        self.player.armor += armor
        self.hud.update_armor(self.player.armor)
        self.hud.update_cost(self.player.cost)

    def enemy_attack(self, add_damage=0):
        damage = self.enemy.damage + add_damage - self.player.armor
        if damage > 0:
            self.player.hp -= damage
        self.hud.update_player_hp(self.player.hp)
        
    def game_loop(self, elapsed):
        if self.enemy.hp <= 0:
            self.player.position = self.return_pos
            self.enemy.kill()
            # self.movelayer.remove(self.enemy)
            director.pop()
            
        if self.player.cost == 0:
            add_damage = random.randint(1,5)
            self.enemy_attack(add_damage)
            self.delete_cards()
            self.create_cards()
            self.player.cost = 3
            self.player.armor = 0
            self.hud.update_armor(self.player.armor)

        if self.player.hp <= 0:
            self.player.position = self.return_pos
            director.pop()

    def create_cards(self):
        self.collman.clear()
        cards = []
        for i in range(5):
            if self.card_i >= len(self.player.decks):
                random.shuffle(self.player.decks)
                self.card_i = 0
            cards.append(self.player.decks[self.card_i])
            cards[i].position = (0.5 * self.width + 100*(i-2), 0)
            cards[i].cshape.center = (0.5 * self.width + 100*(i-2), 0)
            self.add(cards[i])
            self.collman.add(cards[i])
            self.card_i += 1

    def delete_cards(self):
        for _, node in self.children:
            if isinstance(node, actors.Card):
                node.kill()
            
class Battle_HUD(cocos.layer.Layer):
    def __init__(self):
        super(Battle_HUD, self).__init__()
        w, h = director.get_window_size()
        self.player_hp = self._create_text(60, h-40)
        self.player_armor = self._create_text(60, h-70)
        self.player_cost = self._create_text(60, h-100)
        self.enemy_hp = self._create_text(w-60, h-40)

    def _create_text(self, x, y):
        text = cocos.text.Label(font_size=18, font_name='Oswald',
                                anchor_x='center', anchor_y='center')
        text.position = (x, y)
        self.add(text)
        return text

    def update_player_hp(self, hp):
        self.player_hp.element.text = 'HP: %s' % hp

    def update_enemy_hp(self, hp):
        self.enemy_hp.element.text = 'HP: %s' % hp

    def update_cost(self, cost):
        self.player_cost.element.text = 'Cost: %s' % cost

    def update_armor(self, armor):
        self.player_armor.element.text = 'Armor: %s' % armor

def new_battle(player, enemy):
    scenario = sc.get_battle_scenario()
    background = scenario.get_background()
    hud = Battle_HUD()
    game_layer = BattleLayer(hud, scenario, player, enemy)
    return cocos.scene.Scene(background, game_layer, hud)