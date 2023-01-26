import sys
from api.enemy import Enemy

from math import ceil

def endurance_bar(entity) :
    """Entrée : type Character ou Enemy
    Sortie : type String"""

    # Nombre total de carrés de couleur composant la barre de vie
    total_char_number = 8

    filling_char = "\N{LARGE GREEN SQUARE}"
    background_char = "\N{LARGE RED SQUARE}"

    hp_ratio = entity.hp / entity.max_hp

    filling_char_number = ceil(hp_ratio * total_char_number)
    background_char_number = total_char_number - filling_char_number

    result = filling_char_number * filling_char
    result += background_char_number * background_char

    return result

def xp_bar(entity) :
    """Entrée : type Character ou Enemy
    Sortie : type String"""

    # Nombre total de carrés de couleur composant la barre de vie
    total_char_number = 8

    filling_char = "\N{LARGE GREEN SQUARE}"
    background_char = "\N{LARGE PURPLE SQUARE}"

    xp_ratio = entity.xp / (12+((entity.level)+1)**3)

    filling_char_number = ceil(xp_ratio * total_char_number)
    background_char_number = total_char_number - filling_char_number
    result = filling_char_number * filling_char
    result += background_char_number * background_char

    if len(result) > total_char_number:
        result = result[:-(len(result)-total_char_number)]

    return result

# Helper functions
def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)
