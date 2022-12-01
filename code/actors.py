import math
from collections import defaultdict
import random

from pyglet.window import key

import cocos.sprite
import cocos.audio
import cocos.actions as ac
import cocos.euclid as eu
import cocos.collision_model as cm
from cocos.director import director

import pyglet.image
from pyglet.image import Animation

player_img = 'assets/tank.png'
goblin_img = 'assets/tank.png'

class Actor(cocos.sprite.Sprite):
    def __init__(self, img, x, y):
        super(Actor, self).__init__(img, position=(x, y))
        self._cshape = cm.CircleShape(self.position,
                                      self.width * 0.5)

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
        super(Player, self).__init__(player_img, x, y)
        self.speed = eu.Vector2(100, 100)
        self.maxhp = 70
        self.hp = self.maxhp
        self.armor = 0
        self.cost = 3
        self._experience = 0
        self.decks = [Attack(self), Attack(self), Attack(self), Attack(self), Attack(self), Defense(self), Defense(self), Defense(self), Defense(self), Defense(self)]

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self, exp):
        self._experience += exp

    def update(self, elapsed):
        pressed = Player.KEYS_PRESSED

        x = pressed[key.D] - pressed[key.A]
        y = pressed[key.W] - pressed[key.S]

        if x != 0 or y != 0:
            pos = self.position

            new_x = pos[0] + self.speed.x * x * elapsed
            w = self.width * 0.5
            new_y = pos[1] + self.speed.y * y * elapsed
            h = self.height * 0.5

            if w <= new_x <= 1600 - w and h <= new_y <= 1600 - h:
                self.position = (new_x, new_y)
            self.cshape.center = self.position

    def collide(self, other):
        if isinstance(other, Enemy):
            return True
        return False

class Enemy(Actor):
    def __init__(self, img, x, y):
        super(Enemy, self).__init__(img, x, y)

    def gen_damage(self):
        pass

class Goblin(Enemy):
    def __init__(self, x, y):
        super(Goblin, self).__init__(goblin_img, x, y)
        self.speed = eu.Vector2(100,100)
        self.hp = 50
        self.base_damage = 10
        self.gen_damage()

    def gen_damage(self):
        self.damage = self.base_damage + random.randint(1, 5)

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