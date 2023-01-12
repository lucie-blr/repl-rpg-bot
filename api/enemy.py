import enum, random, sys, yaml, os
from copy import deepcopy

from api.actor import Actor

class Enemy(Actor):

    def __init__(self, enemy): #name, max_hp, attack, defense, xp, gold
        enemy_db = yaml.safe_load(open(f'./database/enemys/{enemy}.yml'))

        name = enemy_db.get('name')
        max_hp = enemy_db.get('max_hp')
        attack = enemy_db.get('attack')
        defense = enemy_db.get('defense')
        xp = enemy_db.get('xp')
        gold = enemy_db.get('gold')
        self.min_level = enemy_db.get('min_level')

        super().__init__(name, max_hp, max_hp, attack, defense, xp, gold)
        self.enemy = enemy_db.get("enemy")

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
