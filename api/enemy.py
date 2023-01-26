import enum, random, sys, yaml, os
from copy import deepcopy

from api.actor import Actor

class Enemy(Actor):

    def __init__(self, name, hp, max_hp, attack, defense, xp, gold, min_level, enemy, last_death, respawn, adb, battling, skin, battle_message): #name, max_hp, attack, defense, xp, gold

        self.min_level = min_level
        self.enemy = enemy
        self.last_death = last_death
        self.respawn = respawn
        self.battling = battling
        self.skin = skin
        self.battle_message = battle_message

        super().__init__(name, hp, max_hp, attack, defense, xp, gold, adb)

    def rehydrate(self, name, hp, max_hp, attack, defense, xp, gold, enemy, min_level):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense
        self.xp = xp
        self.gold = gold
        self.min_level = min_level
        self.enemy = enemy
        self.last_death = last_death
        self.respawn = respawn
