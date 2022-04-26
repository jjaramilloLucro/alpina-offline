from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Boolean, JSON, inspect
from database import Base

from sqlalchemy.ext.declarative import as_declarative

@as_declarative()
class Base:
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True,  index=True)
    name = Column(String)
    challenge = Column(Integer, ForeignKey("challenges.challenge_id"))

class Challenge(Base):
    __tablename__ = "challenges"

    challenge_id = Column(Integer, primary_key=True,  index=True)
    name = Column(String)
    duration = Column(Integer)
    expire = Column(DateTime(timezone=True))
    tasks = Column(JSON, nullable=True)

class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True,  index=True)
    password = Column(String)
    name = Column(String)
    group = Column(JSON)
    version = Column(String)
    role = Column(String)
    isActive = Column(Boolean)
    team = Column(String)

class Stores(Base):
    __tablename__ = "stores"

    client_id = Column(String, primary_key=True,  index=True)
    user_id = Column(String, ForeignKey("users.username"), nullable=False)
    zone_id = Column(String)
    name = Column(String)
    city = Column(String)
    direction = Column(String)
    category = Column(String)
    tipology = Column(String)
    day_route = Column(JSON)
    add_exhibition = Column(JSON)
    channel = Column(String)
    subchannel = Column(String)
    chain_distributor = Column(String)
    leader = Column(String)
    group = Column(String)

class Essentials(Base):
    __tablename__ = "essentials"

    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)
    prods = Column(JSON)

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True,  index=True)
    session_id = Column(String)
    uid = Column(String, ForeignKey("users.username"), nullable=False)
    document_id = Column(String)
    created_at = Column(DateTime(timezone=True))
    lat = Column(Float)
    lon = Column(Float)
    store = Column(String)
    id_task = Column(Integer)
    imgs = Column(JSON)
    resp = Column(String)

class Missings(Base):
    __tablename__ = "missings"

    session_id = Column(String, primary_key=True)
    finished_at = Column(DateTime(timezone=True))
    products = Column(JSON)

class Images(Base):
    __tablename__ = "images"

    resp_id = Column(String, primary_key=True,  index=True)
    session_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    original_url = Column(String)
    mark_url = Column(String)
    error = Column(String)
    data = Column(JSON)
    schema = Column(String)

class Comments(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True,  index=True)
    session_id = Column(String, nullable=False)
    img_id = Column(String)
    user_id = Column(String, ForeignKey("users.username"))
    created_at = Column(DateTime(timezone=True))
    event = Column(String)
    comment = Column(String)