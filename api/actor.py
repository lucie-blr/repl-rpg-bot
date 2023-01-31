import enum, random, sys, yaml
from copy import deepcopy
from api.gamemode import GameMode

class Actor:

    def __init__(self, name, hp, max_hp, attack, defense, xp, gold, adb):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.adb = adb
        self.defense = defense
        self.xp = xp
        self.gold = gold

    def fight(self, other, attack = None):
        
        attack_rdm = random.randint(self.attack[0], self.attack[1])
        if attack == None:
            damage = round(self.adb * (round(attack_rdm / 10) / 10))

            other.hp -= damage

            return (damage, other.hp <= 0, None) #(damage, fatal)
        else:
            effects = attack.effects
            damage = effects.get("instant_damage")
            other.hp -= damage
            return (damage, other.hp <= 0, attack)
