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
    Unranked = "Unranked"

class TransferType(Enum):
    PLAYER_LEAVE = 0
    PLAYER_JOIN = 1
    TEAM_CREATE = 2
    TEAM_DISBAND = 3
    
