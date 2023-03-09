import enum, random, sys, yaml, os, time
from copy import deepcopy

from api.gamemode import *
from api.enemy import Enemy
from api.actor import Actor
from api.helper_function import *
from api.area import *
from api.spell import *

class Character(Actor):

    level_cap = 10

    def __init__(self, name, hp, max_hp, attack, defense, mana, level, xp, 
    gold, inventory, mode, battling, user_id, area_id,skin, adb, spells, max_mana, defeated):
        super().__init__(name, hp, max_hp, attack, defense, xp, gold, adb)
        self.mana = mana
        self.max_mana = max_mana
        self.level = level
        
        self.inventory = inventory 

        self.mode = GameMode[mode[0]]

        self.battling = battling

        self.user_id = user_id

        self.area_id = area_id

        self.skin = skin
        
        self.spells = {}
        for spell in spells:
            self.spells[spell] = Spell(spell)
        self.defeated = defeated

    def save_to_db(self):

        character_dict = deepcopy(vars(self))
        if self.battling != None:
            self.battling = None
            self.mode = GameMode.ADVENTURE
        character_dict["battling"] = self.battling
        character_dict['mode'] = [self.mode.name]
        
        l = []
        for spell in self.spells.keys():
            l.append(spell)
        
        character_dict['spells'] = l

        db = character_dict
        try:
            with open(f'./database/characters/{self.user_id}.yml', "w") as f:
                yaml.dump(db, f)
        except:
            f = open(f'./database/characters/{self.user_id}.yml', 'x')
            f.close()
            with open(f'./database/characters/{self.user_id}.yml', "w") as f:
                yaml.dump(db, f)

    def fight(self, enemy, attack = None):
        area = Area(self.area_id)

        outcome, killed, attack = super().fight(enemy, attack)

        enemy.battling[self.user_id] += outcome
        
        return outcome, killed, attack

    def flee(self, enemy):
        if random.randint(0,1+self.defense): # flee unscathed
            damage = 0
        else: # take damage
            attack = random.randint(enemy.attack[0], enemy.attack[1])
            damage = round(enemy.adb * (round(attack / 10) / 10))
            self.hp -= damage

        
        area = Area(self.area_id)

        enemy.battling.pop(self.user_id, None)
        
        # Exit battle mode
        self.battling = None
        self.mode = GameMode.ADVENTURE
        return (damage, self.hp <= 0, None) #(damage, killed)

    def defeat(self, enemy):
        if self.level < self.level_cap: # no more XP after hitting level cap
            self.xp += enemy.xp

        self.gold += enemy.gold # loot enemy

        try:
            self.defeated[enemy.enemy] += 1
        except KeyError:
            self.defeated[enemy.enemy] = 1

        # Exit battle mode
        self.battling = None
        self.mode = GameMode.ADVENTURE

        # Check if ready to level up after earning XP
        ready, _ = self.ready_to_level_up()
        
        return (enemy.xp, enemy.gold, ready)

    def ready_to_level_up(self):
        if self.level == 99: # zero values if we've ready the level cap
            return (False, 0)
            
        xp_needed = 12+((self.level)+1)**3
        return (self.xp >= xp_needed, xp_needed-self.xp) #(ready, XP needed)

    def level_up(self, increase):
        ready, xp_needed = self.ready_to_level_up()
        if not ready:
            return (False, self.level) # (not leveled up, current level)
            
        self.xp -= (xp_needed + self.xp)

        self.level += 1 # increase level
        self.max_hp = 20+(self.level-1)**2 
        setattr(self, increase, getattr(self, increase)+1) # increase chosen stat

        self.hp = self.max_hp #refill HP

        return (True, self.level) # (leveled up, new level)

    def die(self):
        self.hp = 0
        self.mode = GameMode.DEAD

    def get_spells(self):
        dic = {}
        for spell in self.spells:
            dic[spell] = Spell(spell)
        
        return dic