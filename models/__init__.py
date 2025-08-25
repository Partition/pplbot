from models.player import Player
from models.account import Account
from models.team import Team
from models.invite import Invite
from models.transfer import Transfer
from models.strike import Strike

from sqlalchemy.orm import configure_mappers
configure_mappers()
# This ensures all models are loaded before any relationships are configured
