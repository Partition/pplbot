from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from .base import Base

class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.discord_id"))
    activity = Column(Boolean)
    team_name = Column(String, ForeignKey("teams.name"))
    transfer_date = Column(DateTime, server_default=func.now())