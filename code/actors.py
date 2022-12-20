import math
from collections import defaultdict
import random

from pyglet.image import load, ImageGrid, Animation
from pyglet.window import key

import cocos.sprite
import cocos.audio
import cocos.actions as ac
import cocos.euclid as eu
import cocos.collision_model as cm
from cocos.director import director

import pyglet.image
from pyglet.image import Animation

def load_animation(image, row=3, col=1, dur=0.1):
    seq = ImageGrid(load(image), row, col)
    return Animation.from_image_sequence(seq, dur)

class Actor(cocos.sprite.Sprite):
    def __init__(self, img, x, y):
        super(Actor, self).__init__(img, position=(x, y))
        self._cshape = cm.AARectShape(self.position,
                                     self.width * 0.5,
                                     self.height * 0.5)

    @property #getter
    def cshape(self):
        self._cshape.center = eu.Vector2(self.x, self.y)
        return self._cshape

    def update(self, elapsed):
        pass

    def collide(self, other):
        pass

class Player(Actor):
    KEYS_PRESSED = defaultdict(int)

    def __init__(self, x ,y):
        super(Player, self).__init__(Player.ANIME['IDLE'], x, y)
        self.scale = 4
        self.speed = eu.Vector2(200, 200)
        self.maxhp = 70
        self.hp = self.maxhp
        self.armor = 0
        self.cost = 3
        self._experience = 0
        self.decks = [Attack(self), Attack(self), Attack(self), Attack(self), Attack(self), Defense(self), Defense(self), Defense(self), Defense(self), Defense(self)]

    ANIME = {
        'UP': load_animation('player_move/player_up.png'),
        'LEFT': load_animation('player_move/player_left.png'),
        'RIGHT': load_animation('player_move/player_right.png'),
        'DOWN': load_animation('player_move/player_down.png'),
        'IDLE': load_animation('player_move/player_down.png'),
        'BATTLE': load_animation('player_battle/player_idle.png', 1, 4),
        'ATTACK': load_animation('player_battle/player_attack.png', 1, 6, 0.05)
    }
    
    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self, exp):
        self._experience += exp

    def update(self, elapsed, status):
        if status == 'move':
            pressed = Player.KEYS_PRESSED

            x = pressed[key.D] - pressed[key.A]
            y = pressed[key.W] - pressed[key.S]


            if x != 0 or y!= 0:
                if y != 0:
                    if y == 1 and self.image != Player.ANIME['UP']:
                        self.image = Player.ANIME['UP']
                    elif y == -1 and self.image != Player.ANIME['DOWN']:
                        self.image = Player.ANIME['DOWN']
                elif x != 0:
                    if x == 1 and self.image != Player.ANIME['RIGHT']:
                        self.image = Player.ANIME['RIGHT']
                    elif x == -1 and self.image != Player.ANIME['LEFT']:
                        self.image = Player.ANIME['LEFT']
                pos = self.position

                new_x = pos[0] + self.speed.x * x * elapsed
                w = self.width * 0.5
                new_y = pos[1] + self.speed.y * y * elapsed
                h = self.height * 0.5

                if w <= new_x <= 1600 - w and h <= new_y <= 1600 - h:
                    self.position = (new_x, new_y)
                self.cshape.center = self.position

            else:
                if self.image != Player.ANIME['IDLE']:
                    self.image = Player.ANIME['IDLE']
        elif status == 'battle':
            if self.image != Player.ANIME['BATTLE']:
                self.image = Player.ANIME['BATTLE']
        elif status == 'attack':
            if self.image != Player.ANIME['ATTACK']:
                self.image = Player.ANIME['ATTACK']

    def collide(self, other):
        if isinstance(other, Enemy):
            return True
        return False

class Enemy(Actor):
    def __init__(self, img, x, y):
        super(Enemy, self).__init__(img, x, y)

    def gen_damage(self):
        pass

class Demon(Enemy):
    def __init__(self, x, y):
        super(Demon, self).__init__(Demon.ANIME['IDLE'], x, y)
        self.speed = eu.Vector2(100,100)
        self.hp = 50
        self.base_damage = 10
        self.gen_damage()

    ANIME = {
        'IDLE': load_animation('demon/demon_idle.png', 1, 6),
        'ATTACK': load_animation('demon/demon_attack.png', 1, 11, 0.05)
    }
    def update(self, elapsed, status):
        if status == 'battle':
            if self.image != Demon.ANIME['IDLE']:
                self.image = Demon.ANIME['IDLE']
        elif status == 'attack':
            if self.image != Demon.ANIME['ATTACK']:
                self.image = Demon.ANIME['ATTACK']
    def gen_damage(self):
        self.damage = self.base_damage + random.randint(1, 5)

class Dragon(Enemy):
    def __init__(self, x, y):
        super(Dragon, self).__init__(Dragon.ANIME['IDLE'], x, y)
        self.scale = 5
        self.speed = eu.Vector2(100, 100)
        self.hp = 100
        self.base_damage = 20
        self.gen_damage()

    ANIME = {
        'IDLE': 'dragon/dragon_idle.png'
        'BATTLE': load_animation('dragon/dragon_battle.png', 4, 4)
    }

    def gen_damage(self):
        self.damage = self.base_damage + random.randint(10, 20)

attack_card = 'image/Card/Card.png'
defense_card = 'image/Card/Card.png'

class Card(cocos.sprite.Sprite):
    def __init__(self, img, player):
        super(Card, self).__init__(img)
        self.player = player
        self.scale = 0.15
        self.cost = 1
        self._cshape = cm.CircleShape(self.position,
                                      self.width * 0.5)

    @property #getter
    def cshape(self):
        self._cshape.center = eu.Vector2(self.x, self.y)
        return self._cshape

    def enforce(self):
        pass

    def activate(self):
        pass

    def is_usable(self, remain_cost):
        if remain_cost >= self.cost:
            return True
        return False


class Attack(Card):
    def __init__(self, player):
        super(Attack, self).__init__(attack_card, player)
        self.color = (255, 0, 0)
        self.damage = 6 + self.player.experience
    
    def enforce(self):
        self.damage += self.player.experience

    def activate(self):
        self.parent.attack(self.damage)

class Defense(Card):
    def __init__(self, player):
        super(Defense, self).__init__(defense_card, player)
        self.color = (0, 255, 0)
        self.armor = 5 + self.player.experience

    def enforce(self):
        self.armor += self.player.experience

    def activate(self):
        self.parent.defense(self.armor)

class End_Button(cocos.sprite.Sprite):
    def __init__(self, x, y):
        super(End_Button, self).__init__('assets/range.png')
        self.position = pos = eu.Vector2(x, y)
        self._cshape = cm.CircleShape(pos, self.width/2)

    @property #getter
    def cshape(self):
        self._cshape.center = eu.Vector2(self.x, self.y)
        return self._cshape