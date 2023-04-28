from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Boolean, JSON, inspect
from database import Base
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.declarative import as_declarative

@as_declarative()
class Base:
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

class Clients(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True,  index=True)
    name = Column(String)
    tipology = Column(String)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True,  index=True)
    display_name = Column(String)
    family = Column(String)
    category = Column(String)
    segment = Column(String)
    territory = Column(String)
    brand = Column(String)
    sku = Column(String)
    ean = Column(String)


class Essentials(Base):
    __tablename__ = "essentials"

    client_id = Column(Integer, ForeignKey("clients.client_id"), primary_key=True)
    prod_id = Column(Integer, ForeignKey("products.product_id"), primary_key=True)


class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True,  index=True)
    password = Column(String)
    name = Column(String)
    telephone = Column(String)
    register_at = Column(DateTime(timezone=True), server_default=func.now())
    isActive = Column(Boolean)
    debug = Column(Boolean)
    register_by = Column(String)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String)

    
class Stores(Base):
    __tablename__ = "stores"

    store_key = Column(String, primary_key=True,  index=True)
    client_id = Column(String)
    zone_id = Column(String)
    distributor_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    uid = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String)
    city = Column(String)
    address = Column(String)
    category = Column(String)
    tipology = Column(String)
    channel = Column(String)
    subchannel = Column(String)
    leader = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    isActive = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String)
    key_analitica = Column(String)


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True,  index=True)
    document_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    uid = Column(String, ForeignKey("users.uid"), nullable=False)
    store = Column(String, ForeignKey("stores.store_key"), nullable=False)
    session_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lat = Column(Float)
    lon = Column(Float)
    imgs = Column(JSON)
    endpoint = Column(String)
    key_analitica = Column(String)


class Missings(Base):
    __tablename__ = "missings"

    missings_id = Column(Integer, primary_key=True,  index=True)
    session_id = Column(String)
    prod_id = Column(Integer, ForeignKey("products.product_id"))
    exist = Column(Boolean)
    finished_at = Column(DateTime(timezone=True), server_default=func.now())
    generated = Column(Boolean, default=False)
    complete = Column(Boolean, default=True)


class Images(Base):
    __tablename__ = "images"

    resp_id = Column(String, primary_key=True,  index=True)
    session_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))
    original_url = Column(String)
    mark_url = Column(String)
    error = Column(String)
    data = Column(JSON)
    schema = Column(String)
    migrated = Column(Boolean)


class Comments(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True,  index=True)
    session_id = Column(String)
    img_id = Column(String)
    user_id = Column(String)
    created_at = Column(DateTime(timezone=True))
    event = Column(String)
    comment = Column(String)


class Recognitions(Base):
    __tablename__ = "recognitions"

    recon_id = Column(Integer, primary_key=True,  index=True)
    resp_id = Column(String, ForeignKey("images.resp_id"))
    train_product_id = Column(Integer, ForeignKey("train_products.train_product_id"))
    score = Column(Float)
    bounding_box = Column(JSON)


class Configs(Base):
    __tablename__ = "configs"

    config_id = Column(Integer, primary_key=True,  index=True)
    key = Column(String)
    value = Column(String)


class Train_Product(Base):
    __tablename__ = "train_products"

    train_product_id = Column(Integer, primary_key=True,  index=True)
    prod_id = Column(Integer, ForeignKey("products.product_id"))
    train_name = Column(String)

class Frequent_Stores(Base):
    __tablename__ = "frequent_stores"

    store = Column(String, primary_key=True,  index=True)
    anio = Column(Integer, primary_key=True)
    mes = Column(Integer, primary_key=True)
    conteo_actual = Column(Integer)
    conteo_anterior = Column(Integer)
    frecuente = Column(Boolean)
    recurrente = Column(Boolean)
