from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


class MarketPost(Base):
    __tablename__ = "market_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=True)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    author = relationship("User")
    likes = relationship("MarketPostLike", back_populates="post", cascade="all, delete-orphan")


class MarketPostLike(Base):
    __tablename__ = "market_post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("market_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    post = relationship("MarketPost", back_populates="likes")

    __table_args__ = (UniqueConstraint("user_id", "post_id"),)
