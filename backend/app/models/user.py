"""Модуль определения модели пользователя"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    Определение модели пользователя
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

    books = relationship("Book", back_populates="owner")
    proposed_exchanges = relationship("Exchange", foreign_keys="[Exchange.proposing_user_id]",
                                      back_populates="proposing_user")
    received_exchanges = relationship("Exchange", foreign_keys="[Exchange.receiving_user_id]",
                                      back_populates="receiving_user")

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
