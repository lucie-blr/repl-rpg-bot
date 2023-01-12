import enum, random, sys, yaml, os
from copy import deepcopy

from api.gamemode import GameMode
from api.enemy import Enemy
from api.actor import Actor
from api.helper_function import *

class Character(Actor):

    level_cap = 10

    def __init__(self, name, hp, max_hp, attack, defense, mana, level, xp, gold, inventory, mode, battling, user_id):
        super().__init__(name, hp, max_hp, attack, defense, xp, gold)
        self.mana = mana
        self.level = level
        
        self.inventory = inventory 

        self.mode = GameMode[mode[0]]
        if battling != None:
            enemy_class = battling.get("enemy")
            self.battling = Enemy(enemy_class)
            self.battling.rehydrate(**battling)
        else:
            self.battling = None
        self.user_id = user_id

    def save_to_db(self):
        db = yaml.safe_load(open('./game.yml'))

        character_dict = deepcopy(vars(self))
        if self.battling != None:
            character_dict["battling"] = deepcopy(vars(self.battling))
        character_dict['mode'] = [self.mode.name]

        db["characters"][self.user_id] = character_dict

        with open(f"game.yml", "w") as f:
                yaml.dump(db, f)

    def hunt(self):
        # Generate random enemy to fight
        while True:
            enemy_types = []

            for filename in os.listdir('./database/enemys'):
                enemy_types.append(filename[:-4])

            enemy_type = random.choice(enemy_types)

            enemy_type = Enemy(enemy_type)
    
            if enemy_type.min_level <= self.level:
                break

        enemy = enemy_type

        # Enter battle mode
        self.mode = GameMode.BATTLE
        self.battling = enemy

        # Save changes to DB after state change
        self.save_to_db()

        return enemy

    def fight(self, enemy):
        outcome = super().fight(enemy)
        
        # Save changes to DB after state change
        self.save_to_db()
        
        return outcome

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
        ready, _ = self.ready_to_level_up()
        if not ready:
            return (False, self.level) # (not leveled up, current level)
            
        self.level += 1 # increase level
        self.max_hp = 20+(self.level-1)**2 
        setattr(self, increase, getattr(self, increase)+1) # increase chosen stat

        self.hp = self.max_hp #refill HP
        
        # Save to DB after state change
        self.save_to_db()

        return (True, self.level) # (leveled up, new level)
