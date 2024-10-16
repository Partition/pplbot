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
    Top = "Top"
    Jungle = "Jungle"
    Mid = "Mid"
    Bot = "Bot"
    Support = "Support"
    
class TeamLeague(Enum):
    Prime = "Prime"
    Surrogate = "Surrogate"
    Trine = "Trine"

class TransferType(Enum):
    PLAYER_JOIN = 1
    PLAYER_LEAVE = 2
    TEAM_CREATE = 3
    TEAM_DISBAND = 4
    
