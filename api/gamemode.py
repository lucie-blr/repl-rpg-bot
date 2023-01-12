import enum

class GameMode(enum.IntEnum):
  ADVENTURE = 1
  BATTLE = 2
  DEAD = 3

class ZoneType(enum.IntEnum):
  RP = 1
  CITY = 2
  PVE_ZONE = 3