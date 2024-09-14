from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Strike(Base):
    __tablename__ = "strikes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issued_by_id = Column(Integer, ForeignKey("players.discord_id"))
    issued_for_id = Column(Integer, ForeignKey("players.discord_id"))
    reason = Column(String)
    punishment = Column(String)
    expires_at = Column(DateTime)
    issued_by = relationship("Player", foreign_keys=[issued_by_id], back_populates="strikes_issued")
    issued_for = relationship("Player", foreign_keys=[issued_for_id], back_populates="strikes_received")