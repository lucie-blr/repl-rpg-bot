import enum, random, sys, yaml, os
from copy import deepcopy

class Spell:
    def __init__(self, id):
        db = yaml.safe_load(open(f"./database/spells/{id}.yml"))

        self.name = db.get("name")
        self.id = db.get("id")
        self.effects = db.get("effects")
        self.mana_cost = db.get("mana_cost")

 
