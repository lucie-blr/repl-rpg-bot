import enum, random, sys, yaml, os, time
from copy import deepcopy

from api.gamemode import *
from api.enemy import Enemy
from api.actor import Actor
from api.helper_function import *
from api.area import *

class Character(Actor):

    level_cap = 10

    def __init__(self, name, hp, max_hp, attack, defense, mana, level, xp, 
    gold, inventory, mode, battling, user_id, area_id,skin, adb):
        super().__init__(name, hp, max_hp, attack, defense, xp, gold, adb)
        self.mana = mana
        self.level = level
        
        self.inventory = inventory 

        self.mode = GameMode[mode[0]]

        self.battling = battling

        self.user_id = user_id

        self.area_id = area_id

        self.skin = skin

    def save_to_db(self):

        character_dict = deepcopy(vars(self))
        if self.battling != None:
            character_dict["battling"] = self.battling
        character_dict['mode'] = [self.mode.name]

        db = character_dict
        try:
            with open(f'./database/characters/{self.user_id}.yml', "w") as f:
                yaml.dump(db, f)
        except:
            f = open(f'./database/characters/{self.user_id}.yml', 'x')
            f.close()
            with open(f'./database/characters/{self.user_id}.yml', "w") as f:
                yaml.dump(db, f)

    def hunt(self):
        # Generate random enemy to fight
        enemys = []

        area = Area(self.area_id)

        entitys = area.entitys

        if area.type == AreaType.PVE_AREA:
            for entity in area.entitys.keys():

                entity_dict = area.entitys.get(entity)

                print(time.time() - entity_dict["last_death"])
                print(entity_dict["respawn"])

                if time.time() - entity_dict["last_death"] >= entity_dict["respawn"]:

                    enemys.append(entity)

        if len(enemys) <= 0:
            return None

        enemy = random.choice(enemys)

        # Enter battle mode
        self.mode = GameMode.BATTLE
        self.battling = enemy

        enemy_dict = area.entitys.get(enemy)

        player = enemy_dict.get("battling")

        player[self.user_id] = 0

        area.entitys.pop(enemy, None)
        area.battling[enemy] = enemy_dict

        # Save changes to DB after state change
        self.save_to_db()
        area.save_to_db()

        return enemy

    def fight(self, enemy):
        area = Area(self.area_id)

        enemy_dict = area.battling.get(self.battling)

        enemy = Enemy(**enemy_dict)

        outcome, killed = super().fight(enemy)
        
        # Save changes to DB after state change
        self.save_to_db()

        area.save_enemy(enemy, self.battling)

        area.save_to_db()
        
        return outcome, killed

    def flee(self, enemy):
        if random.randint(0,1+self.defense): # flee unscathed
            damage = 0
        else: # take damage
            damage = enemy.attack/2
            self.hp -= damage

        # Exit battle mode
        self.battling = None
        self.mode = GameMode.ADVENTURE

        # Save to DB after state change
        self.save_to_db()

        return (damage, self.hp <= 0) #(damage, killed)

    def defeat(self, enemy):
        if self.level < self.level_cap: # no more XP after hitting level cap
            self.xp += enemy.xp

        self.gold += enemy.gold # loot enemy

        # Exit battle mode
        self.battling = None
        self.mode = GameMode.ADVENTURE

        # Check if ready to level up after earning XP
        ready, _ = self.ready_to_level_up()

        # Save to DB after state change
        self.save_to_db()
        
        return (enemy.xp, enemy.gold, ready)

    def ready_to_level_up(self):
        if self.level == self.level_cap: # zero values if we've ready the level cap
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
        
        # Save to DB after state change
        self.save_to_db()

        return (True, self.level) # (leveled up, new level)

    def die(self):
        self.hp = 0
        self.mode = GameMode.DEAD
        self.save_to_db()