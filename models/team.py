from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, BigInteger, or_, join
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, select
import models
from .base import Base

class TeamAlreadyExists(Exception):
    pass

class TeamNameAlreadyExists(Exception):
    pass

class TeamTagAlreadyExists(Exception):
    pass

class Team(Base):
    __tablename__ = "teams_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    tag = Column(String(5), unique=True)
    league = Column(String)
    captain_id = Column(BigInteger, ForeignKey("players_table.discord_id"), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    tokens_available = Column(Integer)
    active = Column(Boolean, default=True)

    # One-to-many relationship with Player (players in a team)
    players = relationship("Player", back_populates="team", foreign_keys="[Player.team_id]")
    # One-to-one relationship with captain (specific player as captain)
    captain = relationship("Player", back_populates="captained_team", foreign_keys=[captain_id], uselist=False)
    transfers = relationship("Transfer", back_populates="team")
    strikes_received = relationship("Strike", foreign_keys="Strike.issued_for_team_id", back_populates="issued_for_team")
    
    @classmethod
    async def name_or_tag_exists(cls, session: AsyncSession, name: str, tag: str) -> bool:
        result = await session.execute(
            select(cls).where(or_(cls.name == name, cls.tag == tag))
        )
        return result.scalars().first() is not None

    @classmethod
    async def name_exists(cls, session: AsyncSession, name: str) -> bool:
        result = await session.execute(select(cls).where(cls.name == name))
        return result.scalars().first() is not None

    @classmethod
    async def tag_exists(cls, session: AsyncSession, tag: str) -> bool:
        result = await session.execute(select(cls).where(cls.tag == tag))
        return result.scalars().first() is not None

    @classmethod
    async def create(cls, session: AsyncSession, name: str, tag: str, captain_id: int, league: str) -> "Team":
        if await cls.name_exists(session, name):
            raise TeamNameAlreadyExists(f"Team name '{name}' already exists")
        
        if await cls.tag_exists(session, tag):
            raise TeamTagAlreadyExists(f"Team tag '{tag}' already exists")
        
        team = cls(name=name, tag=tag, captain_id=captain_id, league=league)
        session.add(team)
        await session.flush()
        return team

    
    @classmethod
    async def archive(cls, session: AsyncSession, team_id: int):
        team = await session.get(cls, team_id)
        if team:
            team.captain_id = None
            team.active = False
            await session.flush()

    # Fetchers
    @classmethod
    async def fetch_from_id(cls, session: AsyncSession, team_id: int):
        team = await session.get(cls, team_id)
        return team

    @classmethod
    async def fetch_from_name(cls, session: AsyncSession, name: str):
        team = await session.execute(select(cls).where(cls.name == name))
        return team.scalars().first()
    
    @classmethod
    async def fetch_from_tag(cls, session: AsyncSession, tag: str):
        team = await session.execute(select(cls).where(cls.tag == tag))
        return team.scalars().first()
    
    @classmethod
    async def fetch_from_captain_id(cls, session: AsyncSession, captain_id: int):
        team = await session.execute(select(cls).where(cls.captain_id == captain_id))
        return team.scalars().first()

    @classmethod
    async def fetch_all(cls, session: AsyncSession):
        teams = await session.execute(select(cls).where(cls.active == True))
        return teams.scalars().all()
    
    @classmethod
    async def fetch_all_from_league(cls, session: AsyncSession, league: str):
        teams = await session.execute(select(cls).where(cls.league == league))
        return teams.scalars().all()

    @classmethod
    async def fetch_by_player_discord_id(cls, session: AsyncSession, discord_id: int):
        result = await session.execute(
            select(cls)
            .join(models.Player, models.Player.team_id == cls.id)
            .where(models.Player.discord_id == discord_id)
        )
        return result.scalars().first()

