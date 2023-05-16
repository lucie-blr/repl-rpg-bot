import enum, random, sys, yaml, os
from copy import deepcopy

class Item():
    def __init__(self, id):
        db = yaml.safe_load(open(f"./database/items/{id}.yml"))
        self.name = db.get("name")
        self.id = id
        self.description = db.get("description")
        self.bonus = db.get("bonus")
        self.type = db.get("type") 
