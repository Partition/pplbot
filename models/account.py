from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.discord_id"), nullable=False)
    username = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    server = Column(String, nullable=False)
    added_at = Column(DateTime, server_default=func.now())
    player = relationship("Player", back_populates="accounts")