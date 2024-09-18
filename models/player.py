from sqlalchemy import Table, Column, BigInteger, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import Base

class PlayerAlreadyInTeam(Exception):
    pass

class PlayerDoesNotExist(Exception):
    pass

class PlayerAlreadyExists(Exception):
    pass

teams_table = Table('teams_table', Base.metadata, autoload_with=Base.metadata.bind)

class Player(Base):
    #TODO: Perhaps remove setters and establish session wrappers and change attrs and commit
    __tablename__ = "players_table"

    discord_id = Column(BigInteger, primary_key=True, unique=True)
    team_id = Column(Integer, ForeignKey("teams_table.id"))
    registered_at = Column(DateTime, server_default=func.now())
    is_premium = Column(Boolean, default=False)
    bio = Column(String(100))
    role = Column(String(5))

    # Many-to-one relationship with Team
    team = relationship("Team", back_populates="players", foreign_keys=[team_id])

    # One-to-one relationship with captain (specific player as captain)
    captained_team = relationship("Team", back_populates="captain", foreign_keys="Team.captain_id", uselist=False)

    invites_sent = relationship("Invite", foreign_keys="Invite.inviter_id", back_populates="inviter")
    invites_received = relationship("Invite", foreign_keys="Invite.invitee_id", back_populates="invitee")
    transfers = relationship("Transfer", back_populates="player")

    @property
    async def is_captain(self):
        if self.team is None:
            return False
        await self.team
        return self.team.captain_id == self.discord_id
    
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
    
    @classmethod
    async def create(cls, session: AsyncSession, discord_id: int, role: str):
        new_player = cls(discord_id=discord_id, role=role)
        session.add(new_player)
        await session.flush()
        return new_player
    
    # Fetchers
    @classmethod
    async def fetch_from_discord_id(cls, session: AsyncSession, discord_id: int) -> "Player":
        result = await session.get(cls, discord_id)
        if result is None:
            raise PlayerDoesNotExist
        return result

    @classmethod
    async def fetch_all_from_team_id(cls, session: AsyncSession, team_id: int):
        result = await session.execute(select(cls).filter(cls.team_id == team_id))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_from_team_name(cls, session: AsyncSession, team_name: str):
        result = await session.execute(select(cls).join(teams_table).filter(teams_table.c.name == team_name))
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