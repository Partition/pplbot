from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func, select
from sqlalchemy import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from .base import Base
from datetime import datetime

class Transfer(Base):
    __tablename__ = "transfers_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.discord_id"))
    activity = Column(Boolean)
    team_name = Column(String, ForeignKey("teams.name"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    transfer_date = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="transfers")
    team = relationship("Team", back_populates="transfers")
    
    
    @classmethod
    async def create(cls, session: AsyncSession, player_id: int, team_id: int, team_name: str, activity: bool):
        transfer = cls(player_id=player_id, team_id=team_id, team_name=team_name, activity=activity)
        session.add(transfer)
        await session.commit()
        return transfer
    
    @classmethod
    async def fetch_all_transfers(cls, session: AsyncSession):
        transfers = await session.execute(select(cls))
        return transfers.scalars().all()
    
    @classmethod
    async def fetch_all_player_transfers_from_player_id(cls, session: AsyncSession, player_id: int):
        transfers = await session.execute(select(cls).where(cls.player_id == player_id))
        return transfers.scalars().all()
    
    @classmethod
    async def fetch_all_team_transfers_from_team_name(cls, session: AsyncSession, team_name: str):
        transfers = await session.execute(select(cls).where(cls.team_name == team_name))
        return transfers.scalars().all()
    
    @classmethod
    async def fetch_all_team_transfers_from_team_id(cls, session: AsyncSession, team_id: int):
        transfers = await session.execute(select(cls).where(cls.team_id == team_id))
        return transfers.scalars().all()
    
    @classmethod
    async def fetch_all_team_transfers_within_time_period_from_team_id(cls, session: AsyncSession, team_id: int, from_date: datetime, to_date: datetime):
        transfers = await session.execute(select(cls).where(
            cls.team_id == team_id &
            cls.transfer_date >= from_date &
            cls.transfer_date <= to_date
        ))
        return transfers.scalars().all()
