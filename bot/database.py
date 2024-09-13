from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, CHAR
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Construct DATABASE_URL using environment variables
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    discord_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    registered_at = Column(DateTime, server_default=func.now())
    is_premium = Column(Boolean, default=False)
    bio = Column(String(100))
    team = relationship("Team", back_populates="players")
    accounts = relationship("Account", back_populates="player")
    invites_sent = relationship("Invite", foreign_keys="Invite.inviter_id", back_populates="inviter")
    invites_received = relationship("Invite", foreign_keys="Invite.invitee_id", back_populates="invitee")
    strikes_issued = relationship("Strike", foreign_keys="Strike.issued_by_id", back_populates="issued_by")
    strikes_received = relationship("Strike", foreign_keys="Strike.issued_for_id", back_populates="issued_for")


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

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.discord_id"), nullable=False)
    username = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    server = Column(String, nullable=False)
    added_at = Column(DateTime, server_default=func.now())
    player = relationship("Player", back_populates="accounts")
    

class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.discord_id"))
    activity = Column(Boolean)
    team_name = Column(String, ForeignKey("teams.name"))
    transfer_date = Column(DateTime, server_default=func.now())

class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(Integer, ForeignKey("players.discord_id"))
    invitee_id = Column(Integer, ForeignKey("players.discord_id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    created_at = Column(DateTime, server_default=func.now())
    approved = Column(Boolean)
    expires_at = Column(DateTime)
    active = Column(Boolean, default=True)
    inviter = relationship("Player", foreign_keys=[inviter_id], back_populates="invites_sent")
    invitee = relationship("Player", foreign_keys=[invitee_id], back_populates="invites_received")
    team = relationship("Team")

class Strike(Base):
    __tablename__ = "strikes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issued_by_id = Column(Integer, ForeignKey("players.discord_id"))
    issued_for_id = Column(Integer, ForeignKey("players.discord_id"))
    reason = Column(String)
    punishment = Column(String)
    expires_at = Column(DateTime)
    issued_by = relationship("Player", foreign_keys=[issued_by_id], back_populates="strikes_issued")
    issued_for = relationship("Player", foreign_keys=[issued_for_id], back_populates="strikes_received")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

