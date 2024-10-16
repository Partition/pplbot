from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.sql import func, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from .base import Base

class Transfer(Base):
    __tablename__ = "transfers_table"

    id = Column(Integer, primary_key=True)
    player_id = Column(BigInteger, ForeignKey('players_table.discord_id'))
    team_id = Column(Integer, ForeignKey('teams_table.id'))
    role_at_transfer = Column(String)
    transfer_type = Column(Integer)
    transfer_date = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="transfers", foreign_keys=[player_id], lazy="selectin")
    team = relationship("Team", back_populates="transfers", foreign_keys=[team_id], lazy="selectin")
    
    # 0: Player leave
    # 1: Player join
    # 2: Team created
    # 3: Team disbanded
    @classmethod
    async def create(cls, session: AsyncSession, player_id: int, team_id: int, transfer_type: int, role_at_transfer: str):
        transfer = cls(player_id=player_id, team_id=team_id, transfer_type=transfer_type, role_at_transfer=role_at_transfer)
        session.add(transfer)
        await session.flush()
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
