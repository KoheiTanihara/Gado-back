# app/models.py を修正

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String # String をインポート
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # String に長さを指定 (例: 255)
    username = Column(String(255), unique=True, index=True)
    # hashed_password にも長さを指定 (bcryptハッシュは通常60文字なので、余裕をもって255など)
    hashed_password = Column(String(255))
    # email にも長さを指定
    email = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    # title にも長さを指定
    title = Column(String(255), index=True)
    # description にも長さを指定
    description = Column(String(255), index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")