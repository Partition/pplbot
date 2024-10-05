from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, select
from .base import Base
from datetime import datetime, timedelta
from models.team import Team

class Invite(Base):
    __tablename__ = "invites_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(BigInteger, ForeignKey("players_table.discord_id"))
    invitee_id = Column(BigInteger, ForeignKey("players_table.discord_id"))
    team_id = Column(Integer, ForeignKey("teams_table.id"))
    created_at = Column(DateTime, server_default=func.now())
    approved = Column(Boolean)
    approved_by = Column(BigInteger, ForeignKey("players_table.discord_id"))
    approved_at = Column(DateTime)
    expires_at = Column(DateTime)
    active = Column(Boolean, default=True) # False = declined, expired, not approved, True = active
    
    inviter = relationship("Player", foreign_keys=[inviter_id], back_populates="invites_sent")
    invitee = relationship("Player", foreign_keys=[invitee_id], back_populates="invites_received")
    team = relationship("Team")

    @classmethod
    async def create(cls, session: AsyncSession, inviter_id: int, invitee_id: int, team_id: int, expires_at: datetime):
        invite = cls(inviter_id=inviter_id, invitee_id=invitee_id, team_id=team_id, expires_at=expires_at)
        session.add(invite)
        await session.flush()
        return invite
    
    @classmethod
    async def delete(cls, session: AsyncSession, invite_id: int):
        invite = await session.get(cls, invite_id)
        if invite:
            invite.active = False
            await session.flush()
    
    @classmethod
    async def approve_status(cls, session: AsyncSession, invite_id: int, approval: bool):
        invite = await session.get(cls, invite_id)
        if invite:
            invite.approved = approval
            if approval:
                invite.expires_at = datetime.now() + timedelta(days=7)
                invite.approved_by = invite.inviter_id
                invite.approved_at = datetime.now()
            else:
                invite.active = False
            await session.flush()
        return invite
    
    # Fetchters
    @classmethod
    async def fetch_from_id(cls, session: AsyncSession, invite_id: int):
        invite = await session.get(cls, invite_id)
        return invite

    @classmethod
    async def fetch_all_invites_by_invitee(cls, session: AsyncSession, invitee_id: int):
        invites = await session.execute(select(cls).where(cls.invitee_id == invitee_id))
        return invites.scalars().all()
    
    @classmethod
    async def fetch_all_invites_by_inviter(cls, session: AsyncSession, inviter_id: int):
        invites = await session.execute(select(cls).where(cls.inviter_id == inviter_id))
        return invites.scalars().all()
    
    @classmethod
    async def fetch_active_invites_by_invitee(cls, session: AsyncSession, invitee_id: int):
        invites = await session.execute(select(cls).where(cls.invitee_id == invitee_id).where(cls.active == True))
        return invites.scalars().all()

    @classmethod
    async def fetch_active_invites_by_inviter(cls, session: AsyncSession, inviter_id: int):
        invites = await session.execute(select(cls).where(cls.inviter_id == inviter_id).where(cls.active == True))
        return invites.scalars().all()
    
    @classmethod
    async def fetch_active_invite_by_team_id_and_invitee(cls, session: AsyncSession, team_id: int, invitee_id: int):
        invite = await session.execute(select(cls).where(cls.team_id == team_id).where(cls.invitee_id == invitee_id).where(cls.active == True))
        return invite.scalars().first()
    
    @classmethod
    async def fetch_active_invite_by_team_tag_and_invitee(cls, session: AsyncSession, team_tag: str, invitee_id: int):
        invite = await session.execute(select(cls).join(Team).where(Team.tag == team_tag).where(cls.invitee_id == invitee_id).where(cls.active == True))
        return invite.scalars().first()
