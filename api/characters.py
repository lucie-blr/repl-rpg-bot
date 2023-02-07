from api.character import Character
import yaml

class Characters:
    def __init__(self):
        self.characters = {}

    def get(self, player_id):
        return self.characters.get(str(player_id))
    
    def load(self, player_id):

        character_dict = yaml.safe_load(open(f'./database/characters/{player_id}.yml'))

        self.characters[player_id] = Character(**character_dict)

        return self.get(player_id)

    def save(self):
        for character in self.characters.values():
            character.save_to_db()