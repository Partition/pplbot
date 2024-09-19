from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .base import Base

class AccountAlreadyExists(Exception):
    pass

class AccountDoesNotExist(Exception):
    pass

class Account(Base):


    __tablename__ = "accounts_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.discord_id"), nullable=False)
    server = Column(String, nullable=False)
    puuid = Column(String, nullable=False, unique=True)
    added_at = Column(DateTime, server_default=func.now())
    player = relationship("Player", back_populates="accounts")
    
    @classmethod
    async def create(cls, session: AsyncSession, player_id: int, server: str, puuid: str) -> "Account":
        try:
            new_account = cls(player_id=player_id, server=server, puuid=puuid)
            session.add(new_account)
            await session.flush()
            return new_account
        except IntegrityError:
            raise AccountAlreadyExists(f"Account with PUUID {puuid} already exists")

    @classmethod
    async def fetch_from_puuid(cls, session: AsyncSession, puuid: str) -> "Account":
        result = await session.get(cls, puuid)
        if result is None:
            raise AccountDoesNotExist(f"Account with PUUID {puuid} does not exist")
        return result
    
    @classmethod
    async def fetch_all_from_player_id(cls, session: AsyncSession, player_id: int):
        result = await session.execute(select(cls).filter(cls.player_id == player_id))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all(cls, session: AsyncSession):
        result = await session.execute(select(cls))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_from_server(cls, session: AsyncSession, server: str):
        result = await session.execute(select(cls).filter(cls.server == server))
        return result.scalars().all()
    

