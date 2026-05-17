from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, func
from app.database import Base


class UserRecommendation(Base):
    __tablename__ = "user_recommendations"
    __table_args__ = (UniqueConstraint("recommender_id", "recommended_id"),)

    id = Column(Integer, primary_key=True, index=True)
    recommender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recommended_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())