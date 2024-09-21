from .base import Base
from .player import Player
from .account import Account
from .team import Team
from .invite import Invite
from .transfer import Transfer
from .strike import Strike

from sqlalchemy.orm import configure_mappers
configure_mappers()
# This ensures all models are loaded before any relationships are configured
