from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Boolean, JSON
from database import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True,  index=True)
    name = Column(String)
    challenges = Column(JSON)

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

class Stores(Base):
    __tablename__ = "stores"

    client_id = Column(String, primary_key=True,  index=True)
    user_id = Column(String, ForeignKey("users.username"), nullable=False)
    zone_id = Column(String)
    name = Column(String)
    direction = Column(String)
    category = Column(String)
    tipology = Column(String)
    route = Column(String)
    add_exhibition = Column(JSON)

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
    store = Column(Boolean)
    id_task = Column(Integer)
    resp = Column(String)
    imgs = Column(JSON)

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