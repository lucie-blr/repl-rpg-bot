import discord.channel
from api.gamemode import ZoneType
import yaml
from copy import deepcopy

class Zone:
    def __init__(self, channel):
        db = yaml.safe_load(open(f"./database/zones/{channel}.yml"))

        self.name = db.get("name")
        self.description = db.get("description")
        self.channel_id = db.get("channel_id")
        self.entitys = db.get("entitys")
        self.battling = db.get("battling")
        self.type = ZoneType[db.get("type")]
        self.zone = channel

    def save_to_db(self):
        db = yaml.safe_load(open(f'./database/zones/{self.zone}.yml'))

        area_dict = deepcopy(vars(self))

        area_dict['type'] = self.type.name

        db = area_dict

        with open(f"./database/zones/{self.zone}.yml", "w") as f:
            yaml.dump(db, f)

