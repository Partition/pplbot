from sqlalchemy import Column, BigInteger, Boolean, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
Base = declarative_base()

class Guild(Base):
    __tablename__ = "guilds"
    
    guild_id = Column(BigInteger, primary_key=True)
    invite_channel_id = Column(BigInteger, nullable=True)
    transfer_channel_id = Column(BigInteger, nullable=True)  
    
    approval_required = Column(Boolean, default=True)
    
    registered_role_id = Column(BigInteger, nullable=True)
    moderator_role_id = Column(BigInteger, nullable=True)
    
    prime_tokens = Column(Integer, default=0)
    surrogate_tokens = Column(Integer, default=0)
    trine_tokens = Column(Integer, default=0)
    
    prime_role_id = Column(BigInteger, nullable=True)
    surrogate_role_id = Column(BigInteger, nullable=True)
    trine_role_id = Column(BigInteger, nullable=True)
    
    prime_captain_role_id = Column(BigInteger, nullable=True)
    surrogate_captain_role_id = Column(BigInteger, nullable=True)
    trine_captain_role_id = Column(BigInteger, nullable=True)
    
    generic_captain_role_id = Column(BigInteger, nullable=True)
    
    @classmethod
    async def fetch_from_id(cls, session: AsyncSession, guild_id: int):
        guild = await session.get(cls, guild_id)
        return guild
    
    @classmethod
    async def create(cls, session: AsyncSession, guild_id: int):
        guild = cls(guild_id=guild_id)
        session.add(guild)
        await session.flush(guild)
        return guild
    
    
