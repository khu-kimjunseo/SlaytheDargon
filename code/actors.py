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

    def __init__(self, img, x ,y):
        super(Player, self).__init__(img, x, y)
        self.speed = eu.Vector2(100, 100)
        self.maxhp = 70
        self.hp = self.maxhp
        self.armor = 0
        self.cost = 3
        self.decks = [Attack(), Attack(), Attack(), Attack(), Attack(), Defense(), Defense(), Defense(), Defense(), Defense()]
        

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
        self.speed = eu.Vector2(100,100)
        self.hp = 50
        self.damage = 10

attack_card = 'image/Card/Card.png'
defense_card = 'image/Card/Card.png'

class Card(cocos.sprite.Sprite):
    def __init__(self, img):
        super(Card, self).__init__(img)
        self.scale = 0.15
        self.cost = 1
        self._cshape = cm.CircleShape(self.position,
                                      self.width * 0.5)

    @property #getter
    def cshape(self):
        self._cshape.center = eu.Vector2(self.x, self.y)
        return self._cshape

    def activate(self):
        pass


class Attack(Card):
    def __init__(self):
        super(Attack, self).__init__(attack_card)
        self.color = (255, 0, 0)
        self.damage = 6
    
    def activate(self):
        self.parent.attack(self.damage)

class Defense(Card):
    def __init__(self):
        super(Defense, self).__init__(defense_card)
        self.color = (0, 255, 0)
        self.armor = 5

    def activate(self):
        self.parent.defense(self.armor)

"""
raw = pyglet.image.load('assets/explosion.png')
seq = pyglet.image.ImageGrid(raw, 1, 8)
explosion_img = Animation.from_image_sequence(seq, 0.07, False)


class Explosion(cocos.sprite.Sprite):
    def __init__(self, pos):
        super(Explosion, self).__init__(explosion_img, pos)
        self.do(ac.Delay(1) + ac.CallFunc(self.kill))


class Shoot(cocos.sprite.Sprite):
    def __init__(self, pos, offset, target):
        super(Shoot, self).__init__('shoot.png', position=pos)
        self.do(ac.MoveBy(offset, 0.1) +
                ac.CallFunc(self.kill) +
                ac.CallFunc(target.hit))


class Hit(ac.IntervalAction):
    def init(self, duration=0.5):
        self.duration = duration

    def update(self, t):
        self.target.color = (255, 255 * t, 255 * t)

# 콜리전매니저가 마우스와 cshape의 충돌 체크
class TurretSlot(object):
    def __init__(self, pos, side):
        self.cshape = cm.AARectShape(eu.Vector2(*pos), side*0.5, side*0.5) # eu.Vector2(*pos) -> pos

class Turret(Actor):
    def __init__(self, x, y):
        super(Turret, self).__init__('turret.png', x, y)
        self.add(cocos.sprite.Sprite('range.png', opacity=50, scale=5))
        self.cshape.r = 125.0
        self.target = None
        self.period = 2.0
        self.reload = 0.0
        self.schedule(self._shoot)

    def _shoot(self, dt):
        if self.reload < self.period:
            self.reload += dt
        elif self.target is not None:
            self.reload -= self.period
            offset = eu.Vector2(self.target.x - self.x,
                                self.target.y - self.y)
            pos = self.cshape.center + offset.normalized() * 20
            self.parent.add(Shoot(pos, offset, self.target))

    def collide(self, other):
        self.target = other
        if self.target is not None:
            x, y = other.x - self.x, other.y - self.y
            angle = -math.atan2(y, x)
            self.rotation = math.degrees(angle)


class Enemy(Actor):
    def __init__(self, x, y, actions):
        super(Enemy, self).__init__('tank.png', x, y)
        self.health = 100
        self.score = 20
        self.destroyed = False
        self.do(actions)

    def hit(self):
        self.health -= 25
        self.do(Hit())
        if self.health <= 0 and self.is_running:
            self.destroyed = True
            self.explode()

    def explode(self):
        self.parent.add(Explosion(self.position))
        self.kill()


class Bunker(Actor):
    def __init__(self, x, y):
        super(Bunker, self).__init__('bunker.png', x, y)
        self.hp = 100

    def collide(self, other):
        if isinstance(other, Enemy):
            self.hp -= 10
            other.explode()
        if self.hp <= 0:
            self.kill()

"""