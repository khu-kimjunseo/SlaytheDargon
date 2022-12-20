import random

from pyglet.window import key

from cocos.director import director
from cocos.scenes.transitions import TurnOffTilesTransition
import cocos.layer
import cocos.scene
import cocos.sprite
import cocos.text
import cocos.actions as ac
import cocos.collision_model as cm

import actors
import mainmenu
import scenario as sc


class MoveLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True

    def on_key_press(self, k, _):
        actors.Player.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        actors.Player.KEYS_PRESSED[k] = 0

    def __init__(self, hud, scenario):
        super(MoveLayer, self).__init__()
        
        self.hud = hud
        w, h = director.get_window_size()
        px_w, px_h = scenario.get_map_size()

        self.player = actors.Player(px_w * 0.5, 50)
        self.add(self.player)

        self.enemy = []
        for i in range(10):
            x = random.randint(0, px_w)
            y = random.randint(200, px_h)
            self.enemy.append(actors.Demon(x, y))
            self.add(self.enemy[i])

        self.dragon = actors.Dragon(200, px_h-200)
        self.add(self.dragon)

        cell_size = 32
        self.collman = cm.CollisionManagerGrid(0, px_w, 0, px_h, cell_size, cell_size)
        self.schedule(self.game_loop)

    def game_loop(self, elapsed):
        self.player.update(elapsed, 'move')
        self.parent.set_focus(self.player.position[0], self.player.position[1])

        self.collman.clear()
        for _, node in self.children:
            self.collman.add(node)
            # if not self.collman.knows(node):
                # self.remove(node)
        for _, node in self.children:
            if isinstance(node, actors.Player):
                enemy = self.collide(node)
                if enemy is not None:
                    director.push(TurnOffTilesTransition(new_battle(node, enemy), duration=2))
        
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
    scroller = cocos.layer.ScrollingManager()
    scroller.add(background)
    scroller.add(game_layer, z=1)
    return cocos.scene.Scene(scroller, hud)

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

    PLAYER = 1
    ENEMY = -1

    def on_key_press(self, k, _):
        if self.enemy.hp <= 0:
            self.player.position = self.return_pos
            director.pop()

    def on_mouse_press(self, x, y, buttons, mod):
        if self.enemy.hp > 0:
            objs = self.collman.objs_touching_point(x, y)
            if len(objs):
                if isinstance(next(iter(objs)), actors.Card) and self.turn == BattleLayer.PLAYER:
                    card = next(iter(objs))
                    if card.is_usable(self.player.cost) == True:
                        self.player.cost -= card.cost
                        card.activate()
                        card.kill()
                elif isinstance(next(iter(objs)), actors.End_Button) and self.turn == BattleLayer.PLAYER:
                    self.turn_delay = 0
                    self.turn = BattleLayer.ENEMY
                    BattleLayer.is_event_handler = False

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

        self.end_delay = 0
        self.turn_delay = 0
        self.end_button = actors.End_Button(w * 0.8, h * 0.2)
        self.add(self.end_button)
        self.turn = BattleLayer.PLAYER
        # self.movelayer = director.scene_stack[-1]

        self.return_pos = self.player.position

        self.player.position = (200, 0.5*self.height)
        self.player.cshape.center = (200, 0.5*self.height)
        self.enemy.position = (self.width-200, 0.7*self.height)
        self.enemy.cshape.center = (self.width-200, 0.7*self.height)
        self.enemy.scale = 3
        self.card_i = 0
        random.shuffle(self.player.decks)
        
        self.hud.update_enemy_hp(self.enemy.hp)
        self.hud.update_enemy_damage(self.enemy.damage)
        self.hud.update_player_hp(self.player.hp)
        self.hud.update_armor(self.player.armor)
        self.hud.update_cost(self.player.cost)

        cell_size = 32
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        self.schedule(self.game_loop)

        self.create_cards()

    def attack(self, damage=0):
        if damage != 0:
            self.player.do(ac.MoveBy((200,0), duration=0.125) + ac.MoveBy((-200,0), duration=0.125))
            self.player.update(0, 'attack')
        self.enemy.hp -= damage
        self.hud.update_enemy_hp(self.enemy.hp)
        self.hud.update_cost(self.player.cost)
        # 적을 물리쳤을 때 콜되는 함수로 빼기
        if self.enemy.hp <= 0:
            self.enemy.do(ac.FadeOut(1))
            self.player.experience = 1
            self.player.cost = 3
            for card in self.player.decks:
                card.enforce()

    def defense(self, armor=0):
        self.player.armor += armor
        self.hud.update_armor(self.player.armor)
        self.hud.update_cost(self.player.cost)

    def enemy_attack(self):
        self.enemy.do(ac.Delay(1) + ac.MoveBy((-100, 0), duration = 0.4) + ac.MoveBy((100, 0), duration = 0.4))
        damage = self.enemy.damage - self.player.armor
        if damage > 0:
            self.player.hp -= damage
        
        
    def game_loop(self, elapsed):
        if self.player.position == (200, 0.5*self.height):
            self.player.update(0, 'battle')
        else:
            self.player.update(0, 'attack')

        if self.enemy.hp <= 0:
            self.end_delay += elapsed
            BattleLayer.is_event_handler = False
            if self.end_delay >= 1.5:
                win = Win_HUD()
                self.parent.add(win)
                BattleLayer.is_event_handler = True
            # self.enemy.kill()
            # self.movelayer.remove(self.enemy)
            
        if self.turn == BattleLayer.ENEMY:
            if self.turn_delay == 0:
                self.hud.update_turn_msg(self.turn)
                self.enemy_attack()
                self.enemy.update(0, 'attack')
            self.turn_delay += elapsed
            if self.turn_delay >= 1.2:
                self.enemy.update(0, 'battle')
                self.hud.update_player_hp(self.player.hp)
            if self.turn_delay >= 1.6:
                self.enemy.gen_damage()
                self.hud.update_enemy_damage(self.enemy.damage)
                self.delete_cards()
                self.create_cards()
                self.player.cost = 3
                self.hud.update_cost(self.player.cost)
                self.player.armor = 0
                self.hud.update_armor(self.player.armor)

                self.turn = BattleLayer.PLAYER
                self.turn_delay = 0

        if self.turn == BattleLayer.PLAYER:
            if self.turn_delay == 0:
                self.hud.update_turn_msg(self.turn)
            self.turn_delay += elapsed
            

    def create_cards(self):
        self.collman.clear()
        self.collman.add(self.end_button)
        self.cards = []
        for i in range(5):
            if self.card_i >= len(self.player.decks):
                random.shuffle(self.player.decks)
                self.card_i = 0
            self.cards.append(self.player.decks[self.card_i])
            self.cards[i].position = (0.5 * self.width + 100*(i-2), 0)
            self.cards[i].cshape.center = (0.5 * self.width + 100*(i-2), 0)
            self.add(self.cards[i])
            self.collman.add(self.cards[i])
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
        self.enemy_damage = self._create_text(w-60, h-70)

        self.turn_player = self._create_text(w/2, h/2, 40)
        self.turn_player.element.text = 'Your Turn'
        self.turn_player.opacity = 0
        self.turn_enemy = self._create_text(w/2, h/2, 40)
        self.turn_enemy.element.text = 'Enemy Turn'
        self.turn_enemy.opacity = 0

    def _create_text(self, x, y, size = 18):
        text = cocos.text.Label(font_size=size, font_name='Oswald',
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

    def update_enemy_damage(self, damage):
        self.enemy_damage.element.text = 'Damage: %s' % damage
    
    def update_turn_msg(self, turn):
        if turn == BattleLayer.PLAYER:
            self.turn_player.do(ac.FadeIn(0.5) + ac.FadeOut(0.5))
        elif turn == BattleLayer.ENEMY:
            self.turn_enemy.do(ac.FadeIn(0.5) + ac.FadeOut(0.5))

class Win_HUD(cocos.layer.Layer):
    def __init__(self):
        super(Win_HUD, self).__init__()
        w, h = director.get_window_size()
        self.message = self._create_text(w/2, h/2, 40)
        self.message2 = self._create_text(w/2, h/2-45, 25)
        self.message.element.text = 'You Win!'
        self.message2.element.text = 'Press any key to exit.'
    
    def _create_text(self, x, y, size):
        text = cocos.text.Label(font_size=size, font_name='Oswald',
                                anchor_x='center', anchor_y='center')
        text.position = (x, y)
        self.add(text)
        return text

def new_battle(player, enemy):
    scenario = sc.get_battle_scenario()
    background = scenario.get_background()
    hud = Battle_HUD()
    game_layer = BattleLayer(hud, scenario, player, enemy)
    return cocos.scene.Scene(background, game_layer, hud)