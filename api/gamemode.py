import enum

class GameMode(enum.IntEnum):
  ADVENTURE = 1
  BATTLE = 2
  DEAD = 3

class AreaType(enum.IntEnum):
  RP = 1
  CITY = 2
  PVE_AREA = 3