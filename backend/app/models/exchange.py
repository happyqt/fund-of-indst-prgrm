"""Модуль определения модели обмена"""
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Exchange(Base):
    """
    Определение модели обмена
    """
    __tablename__ = 'exchanges'

    id = Column(Integer, primary_key=True, index=True)

    proposing_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiving_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    proposed_book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    requested_book_id = Column(Integer, ForeignKey('books.id'), nullable=False)

    status = Column(String, default='pending', nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    exchange_location = Column(String, nullable=True)

    proposing_user = relationship("User", foreign_keys=[proposing_user_id], back_populates="proposed_exchanges")
    receiving_user = relationship("User", foreign_keys=[receiving_user_id], back_populates="received_exchanges")
    proposed_book = relationship("Book", foreign_keys=[proposed_book_id])
    requested_book = relationship("Book", foreign_keys=[requested_book_id])

    def __repr__(self):
        return (f"<Exchange(id={self.id}, status='{self.status}', "
                f"from_user={self.proposing_user_id} to_user={self.receiving_user_id})>"
                f"location='{self.exchange_location}')>")
