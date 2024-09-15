from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .base import Base
from .team import Team

class Player(Base):
    __tablename__ = "players"

    discord_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    registered_at = Column(DateTime, server_default=func.now())
    is_premium = Column(Boolean, default=False)
    bio = Column(String(100))
    role = Column(String(5))
    team = relationship("Team", back_populates="players")

    @property
    async def is_captain(self):
        if self.team is None:
            return False
        await self.team
        return self.team.captain_id == self.discord_id
    
    @classmethod
    async def create(cls, session: AsyncSession, discord_id: int, role: str):
        new_player = cls(discord_id=discord_id, role=role)
        session.add(new_player)
        await session.commit()
        return new_player
    
    # Setters
    async def set_role(self, session: AsyncSession, role: str):
        self.role = role
        await session.commit()
        return self
    
    async def set_team_id(self, session: AsyncSession, team_id: int):
        self.team_id = team_id
        await session.commit()
        return self
    
    async def set_bio(self, session: AsyncSession, bio: str):
        self.bio = bio
        await session.commit()
        return self
    
    async def set_premium(self, session: AsyncSession, is_premium: bool):
        self.is_premium = is_premium
        await session.commit()
        return self
    
    # Miscellaneous
    async def leave_team(self, session: AsyncSession):
        self.team_id = None
        await session.commit()
        return self
    
    async def to_dict(self):
        return {
            "discord_id": self.discord_id,
            "team_id": self.team_id,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "is_premium": self.is_premium,
            "bio": self.bio,
            "role": self.role,
            "is_captain": await self.is_captain
        }
        
    # Fetchers
    @classmethod
    async def fetch_from_discord_id(cls, session: AsyncSession, discord_id: int):
        result = await session.get(cls, discord_id)
        return result.scalars().first()

    @classmethod
    async def fetch_all_from_team_id(cls, session: AsyncSession, team_id: int):
        result = await session.execute(select(cls).filter(cls.team_id == team_id))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_from_team_name(cls, session: AsyncSession, team_name: str):
        result = await session.execute(select(cls).join(Team).filter(Team.name == team_name))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all(cls, session):
        result = await session.execute(select(cls))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_premium(cls, session: AsyncSession):
        result = await session.execute(select(cls).filter(cls.is_premium == True))
        return result.scalars().all()
    
    @classmethod
    async def count_players(cls, session: AsyncSession):
        result = await session.execute(select(func.count()).select_from(cls))
        return result.scalar_one()

    @classmethod
    async def fetch_players_without_team(cls, session: AsyncSession):
        result = await session.execute(select(cls).filter(cls.team_id == None))
        return result.scalars().all()