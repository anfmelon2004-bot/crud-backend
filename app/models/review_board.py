from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AssignmentLevel(str, enum.Enum):
    many = "many"
    normal = "normal"
    few = "few"
    none = "none"


class Semester(str, enum.Enum):
    first = "1"
    second = "2"
    summer = "summer"
    winter = "winter"


class GradingStyle(str, enum.Enum):
    generous = "generous"
    normal = "normal"
    strict = "strict"


class TeamProjectLoad(str, enum.Enum):
    many = "many"
    normal = "normal"
    few = "few"
    none = "none"


class ReviewPost(Base):
    __tablename__ = "review_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    course_name = Column(String(100), nullable=False)
    professor_name = Column(String(50), nullable=False)
    assignment_level = Column(Enum(AssignmentLevel), nullable=False)
    team_project_load = Column(Enum(TeamProjectLoad), default=TeamProjectLoad.normal, nullable=False)
    grading_style = Column(Enum(GradingStyle), default=GradingStyle.normal, nullable=False)
    rating = Column(Integer, default=5, nullable=False)
    year = Column(Integer, nullable=False)
    semester = Column(Enum(Semester), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    author = relationship("User")
    likes = relationship("ReviewPostLike", back_populates="post", cascade="all, delete-orphan")


class ReviewPostLike(Base):
    __tablename__ = "review_post_likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("review_posts.id"), nullable=False)

    post = relationship("ReviewPost", back_populates="likes")
