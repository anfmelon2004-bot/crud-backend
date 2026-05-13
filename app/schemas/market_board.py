from pydantic import BaseModel
from datetime import datetime


class MarketPostCreate(BaseModel):
    title: str
    content: str
    price: int
    is_anonymous: bool = False


class MarketPostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    price: int | None = None


class MarketPostResponse(BaseModel):
    id: int
    title: str
    content: str
    price: int
    image_path: str | None
    is_anonymous: bool
    author_id: int
    author_name: str
    created_at: datetime
    updated_at: datetime
    like_count: int

    model_config = {"from_attributes": True}


class MarketPostListResponse(BaseModel):
    posts: list[MarketPostResponse]
    total: int
    page: int
    size: int
    total_pages: int
