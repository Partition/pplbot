from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from datetime import datetime, timezone
from .base import Base

class Strike(Base):
    __tablename__ = "strikes_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issued_by_id = Column(Integer, ForeignKey("players.discord_id"))
    issued_for_id = Column(Integer, ForeignKey("players.discord_id"), nullable=True)
    issued_for_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    reason = Column(String)
    punishment = Column(String)
    expires_at = Column(DateTime)
    is_team_strike = Column(Boolean, default=False)
    
    issued_by = relationship("Player", foreign_keys=[issued_by_id], back_populates="strikes_issued")
    issued_for_player = relationship("Player", foreign_keys=[issued_for_id], back_populates="strikes_received")
    issued_for_team = relationship("Team", foreign_keys=[issued_for_team_id], back_populates="strikes_received")

    @classmethod
    async def create_player_strike(cls, session: AsyncSession, issued_by_id: int, issued_for_id: int, reason: str, punishment: str, expires_at: datetime):
        strike = cls(issued_by_id=issued_by_id, issued_for_id=issued_for_id, reason=reason, punishment=punishment, expires_at=expires_at, is_team_strike=False)
        session.add(strike)
        await session.commit()
        return strike

    @classmethod
    async def create_team_strike(cls, session: AsyncSession, issued_by_id: int, issued_for_team_id: int, reason: str, punishment: str, expires_at: datetime):
        strike = cls(issued_by_id=issued_by_id, issued_for_team_id=issued_for_team_id, reason=reason, punishment=punishment, expires_at=expires_at, is_team_strike=True)
        session.add(strike)
        await session.commit()
        return strike

    @classmethod
    async def fetch_all_user_strikes_from_id(cls, session: AsyncSession, issued_for_id: int):
        strikes = await session.execute(select(cls).where(cls.issued_for_id == issued_for_id))
        return strikes.scalars().all()
    
    @classmethod
    async def fetch_active_user_strikes(cls, session: AsyncSession, issued_for_id: int):
        current_time = datetime.now(timezone.utc)
        strikes = await session.execute(
            select(cls).where(
                (
                    (cls.issued_for_id == issued_for_id) &
                    (cls.expires_at > current_time)
                )
            )
        )
        return strikes.scalars().all()

    @classmethod
    async def fetch_all_team_strikes_from_team_id(cls, session: AsyncSession, issued_for_team_id: int):
        strikes = await session.execute(select(cls).where(cls.issued_for_team_id == issued_for_team_id))
        return strikes.scalars().all()
    
    @classmethod
    async def fetch_active_team_strikes(cls, session: AsyncSession, issued_for_team_id: int):
        current_time = datetime.now(timezone.utc)
        strikes = await session.execute(
            select(cls).where(
                (
                    (cls.issued_for_team_id == issued_for_team_id) &
                    (cls.expires_at > current_time)
                )
            )
        )
        return strikes.scalars().all()

    @classmethod
    async def fetch_active_strikes(cls, session: AsyncSession):
        current_time = datetime.now(timezone.utc)
        strikes = await session.execute(
            select(cls).where(
                (
                    (cls.expires_at > current_time)
                )
            )
        )
        return strikes.scalars().all()
    
    @classmethod
    async def fetch_all_strikes(cls, session: AsyncSession):
        strikes = await session.execute(select(cls))
        return strikes.scalars().all()
    
    @classmethod
    async def fetch_all_mod_strikes(cls, session: AsyncSession, issued_by_id: int):
        strikes = await session.execute(select(cls).where(cls.issued_by_id == issued_by_id))
        return strikes.scalars().all()
