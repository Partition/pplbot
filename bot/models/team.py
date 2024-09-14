from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from .base import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    tag = Column(String(100))
    captain_id = Column(Integer, ForeignKey("players.discord_id"))
    created_at = Column(DateTime, server_default=func.now())
    tokens_available = Column(Integer)
    active = Column(Boolean, default=True)
    players = relationship("Player", back_populates="team")
    captain = relationship("Player", foreign_keys=[captain_id])

    @classmethod
    async def create(cls, session: AsyncSession, name: str, tag: str, captain_id: int):
        team = cls(name=name, tag=tag, captain_id=captain_id)
        session.add(team)
        await session.commit()
        return team
    
    @classmethod
    async def delete(cls, session: AsyncSession, team_id: int):
        team = await session.get(cls, team_id)
        if team:
            team.active = False
            await session.commit()

    # Fetchters
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
    

