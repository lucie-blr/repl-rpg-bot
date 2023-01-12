import discord.channel
from api.gamemode import ZoneType
import yaml

class Zone:
    def __init__(self, channel):
        db = yaml.safe_load(open(f"./database/zones/{channel}.yml"))

        self.name = db.get("name")
        self.description = db.get("description")
        self.channel_id = db.get("channel_id")
        self.entitys = db.get("entitys")
        self.type = db.get("type")
        self.zone = channel

