import sys
from api.enemy import Enemy

from math import ceil

def endurance_bar(entity) :
    """Entrée : type Character ou Enemy
    Sortie : type String"""

    # Nombre total de carrés de couleur composant la barre de vie
    total_char_number = 10

    filling_char = "\N{LARGE GREEN SQUARE}"
    background_char = "\N{LARGE RED SQUARE}"

    hp_ratio = entity.hp / entity.max_hp

    filling_char_number = ceil(hp_ratio * total_char_number)
    background_char_number = total_char_number - filling_char_number

    result = filling_char_number * filling_char
    result += background_char_number * background_char
    result += f" **{entity.hp}/{entity.max_hp}**"

    return result

# Helper functions
def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)
