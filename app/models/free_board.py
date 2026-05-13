from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class FreePost(Base):
    __tablename__ = "free_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    image_path = Column(String(500), nullable=True)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    author = relationship("User")
    comments = relationship("FreeComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("FreePostLike", back_populates="post", cascade="all, delete-orphan")


class FreeComment(Base):
    __tablename__ = "free_comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("free_posts.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    author = relationship("User")
    post = relationship("FreePost", back_populates="comments")
    likes = relationship("FreeCommentLike", back_populates="comment", cascade="all, delete-orphan")


class FreePostLike(Base):
    __tablename__ = "free_post_likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("free_posts.id"), nullable=False)

    post = relationship("FreePost", back_populates="likes")


class FreeCommentLike(Base):
    __tablename__ = "free_comment_likes"
    __table_args__ = (UniqueConstraint("user_id", "comment_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("free_comments.id"), nullable=False)

    comment = relationship("FreeComment", back_populates="likes")
