from enum import Enum

class LeagueTier(Enum):
    IRON = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    EMERALD = 5
    DIAMOND = 6
    MASTER = 7
    GRANDMASTER = 8
    CHALLENGER = 9

class LeagueRank(Enum):
    I = 4
    II = 3
    III = 2
    IV = 1

class LeagueServer(Enum):
    EUNE = "eun1"
    EUW = "euw1"

class LeagueRole(Enum):
    TOP = "Top"
    JUNGLE = "Jungle"
    MID = "Mid"
    ADC = "ADC"
    SUPPORT = "Support"


