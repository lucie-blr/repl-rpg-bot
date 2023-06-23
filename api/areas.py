from api.area import Area
import yaml

class Areas:
    def __init__(self):
        self.areas = {}

    def get(self, area_id):
        return self.areas.get(area_id)
    
    def load(self, area_id):

        area_dict = yaml.safe_load(open(f'./database/areas/{area_id}.yml'))

        self.areas[area_id] = Area(area_id)

        return self.get(area_id)

    def save(self):
        for area in self.areas.values():
            area.save_to_db()