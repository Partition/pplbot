from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .base import Base
from datetime import datetime

class AccountAlreadyExists(Exception):
    pass

class AccountDoesNotExist(Exception):
    pass

class Account(Base):
    __tablename__ = "accounts_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(BigInteger, ForeignKey("players_table.discord_id"), nullable=False)
    
    # Account info
    server = Column(String, nullable=False)
    puuid = Column(String, nullable=False, unique=True)
    summoner_name = Column(String, nullable=False)
    summoner_tag = Column(String, nullable=False)
    
    # Ranked info
    summoner_id = Column(String, nullable=False)
    tier = Column(String)
    rank = Column(String)
    league_points = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    peak_tier = Column(String)
    peak_rank = Column(String)
    peak_league_points = Column(Integer)
    peak_occurence = Column(DateTime)
    last_updated = Column(DateTime, server_default=func.now())
    
    # Misc info
    added_at = Column(DateTime, server_default=func.now())
    player = relationship("Player", back_populates="accounts")


    def __str__(self):
        return f"{self.summoner_name}#{self.summoner_tag}"
    
    @classmethod
    async def check_if_username_and_tag_exists(cls, session: AsyncSession, username: str, tag: str, server: str) -> bool:
        result = await session.execute(select(cls).filter(cls.summoner_name == username, cls.summoner_tag == tag, cls.server == server))
        return result.scalars().all()
    
    @classmethod
    async def create(cls, session: AsyncSession, player_id: int, server: str, puuid: str, summoner_name: str, summoner_tag: str, summoner_id: str, **kwargs):
        try:
            account = cls(
            player_id=player_id,
            server=server,
            puuid=puuid,
            summoner_name=summoner_name,
            summoner_tag=summoner_tag,
            summoner_id=summoner_id,
            **kwargs
            )
            session.add(account)
            await session.flush()
            return account
        except IntegrityError:
            raise AccountAlreadyExists(f"Account with PUUID {puuid} already exists")

    @classmethod
    async def fetch_from_puuid(cls, session: AsyncSession, puuid: str) -> "Account":
        result = await session.get(cls, puuid)
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
    

