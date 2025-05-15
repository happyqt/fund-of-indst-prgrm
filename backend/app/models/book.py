from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


"""
Определение модели книги
"""
class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_available = Column(Boolean, default=True)

    owner = relationship("User", back_populates="books")

    proposing_exchange_entries = relationship("Exchange", foreign_keys="[Exchange.proposed_book_id]", viewonly=True)
    receiving_exchange_entries = relationship("Exchange", foreign_keys="[Exchange.requested_book_id]", viewonly=True)

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"
