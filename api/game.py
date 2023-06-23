from api.characters import Characters
from api.areas import Areas
import os

class Game:
    def __init__(self):
        self.characters = Characters()
        self.areas = Areas()

    def loadDb(self):
        for filename in os.listdir('./database/areas'):
            if filename.endswith('.yml'):
                self.areas.load(filename[:-4])
        
        for filename in os.listdir('./database/characters'):
            if filename.endswith('.yml'):
                self.characters.load(filename[:-4])

    def save_to_db(self):
        self.characters.save()
        self.areas.save()