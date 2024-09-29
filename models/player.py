from sqlalchemy import Table, Column, BigInteger, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .base import Base
import models

class PlayerAlreadyInTeam(Exception):
    pass

class PlayerDoesNotExist(Exception):
    pass

class PlayerAlreadyExists(Exception):
    pass

class PlayerNotInTeam(Exception):
    pass

class Player(Base):
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
    strikes_issued = relationship("Strike", foreign_keys="Strike.issued_by_id", back_populates="issued_by")
    strikes_received = relationship("Strike", foreign_keys="Strike.issued_for_id", back_populates="issued_for_player")
    transfers = relationship("Transfer", back_populates="player")
    accounts = relationship("Account", back_populates="player", foreign_keys="Account.player_id")
    
    @property
    async def is_captain(self):
        if self.team is None:
            return False
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
        try:
            new_player = cls(discord_id=discord_id, role=role)
            session.add(new_player)
            await session.flush()
            return new_player
        except IntegrityError:
            raise PlayerAlreadyExists(f"Player with discord ID {discord_id} already exists")

    async def add_to_team(self, session: AsyncSession, team_id: int):
        if self.team_id is not None:
            raise PlayerAlreadyInTeam(f"Player with discord ID {self.discord_id} is already in team {self.team_id}")
        self.team_id = team_id
        await session.flush()
        
    async def remove_from_team(self, session: AsyncSession, team_id: int):
        if self.team_id != team_id:
            raise PlayerNotInTeam(f"Player with discord ID {self.discord_id} is not in team {team_id}")
        self.team_id = None
        await session.flush()

    @classmethod
    async def exists(cls, session: AsyncSession, discord_id: int) -> bool:
        result = await session.get(cls, discord_id)
        return result
    
    # Fetchers
    @classmethod
    async def fetch_from_discord_id(cls, session: AsyncSession, discord_id: int) -> "Player":
        result = await session.get(cls, discord_id)
        return result

    @classmethod
    async def fetch_all_from_team_id(cls, session: AsyncSession, team_id: int):
        result = await session.execute(select(cls).filter(cls.team_id == team_id))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_from_team_name(cls, session: AsyncSession, team_name: str):
        result = await session.execute(select(cls).join(models.Team).filter(models.Team.c.name == team_name))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all(cls, session: AsyncSession):
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