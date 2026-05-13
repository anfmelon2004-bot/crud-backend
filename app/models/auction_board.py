from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


class AuctionPost(Base):
    __tablename__ = "auction_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    course_name = Column(String(100), nullable=False)
    professor_name = Column(String(50), nullable=False)
    starting_price = Column(Integer, nullable=False)
    deadline = Column(DateTime, nullable=False)
    image_path = Column(String(500), nullable=True)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    author = relationship("User")
    bids = relationship("AuctionBid", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("AuctionPostLike", back_populates="post", cascade="all, delete-orphan")


class AuctionBid(Base):
    __tablename__ = "auction_bids"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("auction_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bid_amount = Column(Integer, nullable=False)  # 입찰 총액
    created_at = Column(DateTime, server_default=func.now())

    post = relationship("AuctionPost", back_populates="bids")
    user = relationship("User")


class AuctionPostLike(Base):
    __tablename__ = "auction_post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("auction_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    post = relationship("AuctionPost", back_populates="likes")

    __table_args__ = (UniqueConstraint("user_id", "post_id"),)
