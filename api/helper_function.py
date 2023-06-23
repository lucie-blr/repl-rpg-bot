import sys
from api.enemy import Enemy

from math import ceil

def endurance_bar(entity) :
    """Entrée : type Character ou Enemy
    Sortie : type String"""

    # Nombre total de carrés de couleur composant la barre de vie
    total_char_number = 8

    filling_char = "<:lifebarmiddle:1068151812269551668>"
    background_char = "<:emptybarmiddle:1068151825418702878>"

    hp_ratio = entity.hp / entity.max_hp

    filling_char_number = ceil(hp_ratio * total_char_number-2)
    if filling_char_number < 0:
        filling_char_number = 0

    background_char_number = total_char_number - filling_char_number - 2

    if filling_char_number + background_char_number > total_char_number - 2:
        background_char_number -=  filling_char_number - background_char_number - total_char_number - 2 

    if hp_ratio != 0:
        result = "<:lifebarleft:1068151802085777418>"         
    else:
        result = "<:emptybarleft:1068151816946204742>"
    result += filling_char_number * filling_char
    result += background_char_number * background_char
    if hp_ratio != 1:
        result += "<:emptybarright:1068151820922388510>"
    else:
        result += "<:lifebarright:1068151807903268864>"

    return result

def mana_bar(entity) :
    """Entrée : type Character ou Enemy
    Sortie : type String"""

    # Nombre total de carrés de couleur composant la barre de vie
    total_char_number = 8

    filling_char = "<:manabarmiddle:1069916620421615626>"
    background_char = "<:emptybarmiddle:1068151825418702878>"

    hp_ratio = entity.mana / entity.max_mana

    filling_char_number = ceil(hp_ratio * total_char_number-2)
    if filling_char_number < 0:
        filling_char_number = 0

    background_char_number = total_char_number - filling_char_number - 2

    if filling_char_number + background_char_number > total_char_number - 2:
        background_char_number -=  filling_char_number - background_char_number - total_char_number - 2 

    if hp_ratio != 0:
        result = "<:manabarleft:1069916616361508864>"         
    else:
        result = "<:emptybarleft:1068151816946204742>"
    result += filling_char_number * filling_char
    result += background_char_number * background_char
    if hp_ratio != 1:
        result += "<:emptybarright:1068151820922388510>"
    else:
        result += "<:manabarright:1069916611680686110>"

    return result

def xp_bar(entity) :
    """Entrée : type Character ou Enemy
    Sortie : type String"""

    # Nombre total de carrés de couleur composant la barre de vie
    total_char_number = 8

    filling_char = "<:xpbarmiddle:1068151834914599012>"
    background_char = "<:emptybarmiddle:1068151825418702878>"

    xp_ratio = entity.xp / (12+((entity.level)+1)**3)

    if xp_ratio > 1:
        xp_ratio = 1
        
    filling_char_number = ceil(xp_ratio * total_char_number - 2)
    if filling_char_number < 0:
        filling_char_number = 0

    background_char_number = total_char_number - filling_char_number - 2

    if filling_char_number + background_char_number > total_char_number - 2:
        background_char_number -=  filling_char_number - background_char_number - total_char_number - 2 

    if entity.level == 99:
        xp_ratio = 1
        filling_char_number = total_char_number - 2
        background_char_number = 0


    if xp_ratio != 0:
        result = "<:xpbarleft:1068151839683522610>"
    else:
        result = "<:emptybarleft:1068151816946204742>" 
    result += filling_char_number * filling_char
    result += background_char_number * background_char
    if xp_ratio != 1:
        result += "<:emptybarright:1068151820922388510>"
    else:
        result += "<:xpbarright:1068151830082768916>"
    
    return result

# Helper functions
def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)
