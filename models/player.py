from sqlalchemy import Table, Column, BigInteger, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy.sql import func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from config import NICKNAME_CHARACTER_LIMIT, BIO_CHARACTER_LIMIT
from .base import Base
import models
from typing import Optional
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
    nickname = Column(String(NICKNAME_CHARACTER_LIMIT))
    is_premium = Column(Boolean, default=False)
    bio = Column(String(BIO_CHARACTER_LIMIT))
    role = Column(String)

    # Many-to-one relationship with Team
    team = relationship("Team", back_populates="players", foreign_keys=[team_id], lazy="selectin")

    # One-to-one relationship with captain (specific player as captain)
    captained_team = relationship("Team", back_populates="captain", foreign_keys="Team.captain_id", uselist=False)

    invites_sent = relationship("Invite", foreign_keys="Invite.inviter_id", back_populates="inviter")
    invites_received = relationship("Invite", foreign_keys="Invite.invitee_id", back_populates="invitee")
    strikes_issued = relationship("Strike", foreign_keys="Strike.issued_by_id", back_populates="issued_by")
    strikes_received = relationship("Strike", foreign_keys="Strike.issued_for_id", back_populates="issued_for_player")
    transfers = relationship("Transfer", back_populates="player", lazy="selectin")
    accounts = relationship("Account", back_populates="player", foreign_keys="Account.player_id", lazy="selectin")
    
    @classmethod
    async def is_captain(cls, session: AsyncSession, discord_id: int) -> bool:
        stmt = select(cls).where(cls.discord_id == discord_id).options(joinedload(cls.team))
        result = await session.execute(stmt)
        player = result.scalar_one_or_none()
        
        if player is None or player.team is None:
            return False
        
        return player.team.captain_id == player.discord_id
    
    async def to_dict(self):
        return {
            "discord_id": self.discord_id,
            "team_id": self.team_id,
            "nickname": self.nickname,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "is_premium": self.is_premium,
            "bio": self.bio,
            "role": self.role,
            "is_captain": await self.is_captain
        }
    
    @classmethod
    async def create(cls, session: AsyncSession, discord_id: int, role: str, nickname: str):
        try:
            new_player = cls(discord_id=discord_id, role=role, nickname=nickname)
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
    async def fetch_from_discord_id(cls, session: AsyncSession, discord_id: int) -> Optional["Player"]:
        result = await session.get(cls, discord_id)
        return result

    @classmethod
    async def fetch_all_from_team_id(cls, session: AsyncSession, team_id: int) -> list["Player"]:
        result = await session.execute(select(cls).filter(cls.team_id == team_id))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_from_team_name(cls, session: AsyncSession, team_name: str) -> list["Player"]:
        result = await session.execute(select(cls).join(models.Team).filter(models.Team.c.name == team_name))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all(cls, session: AsyncSession) -> list["Player"]:
        result = await session.execute(select(cls))
        return result.scalars().all()
    
    @classmethod
    async def fetch_all_premium(cls, session: AsyncSession) -> list["Player"]:
        result = await session.execute(select(cls).filter(cls.is_premium == True))
        return result.scalars().all()
    
    @classmethod
    async def count_players(cls, session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(cls))
        return result.scalar_one()

    @classmethod
    async def fetch_players_without_team(cls, session: AsyncSession) -> list["Player"]:
        result = await session.execute(select(cls).filter(cls.team_id == None))
        return result.scalars().all()