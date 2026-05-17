from pydantic import BaseModel


class RecommendResponse(BaseModel):
    recommended: bool
    recommend_count: int


class UserRankingItem(BaseModel):
    user_id: int
    username: str
    recommend_count: int