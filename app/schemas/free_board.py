from pydantic import BaseModel
from datetime import datetime


class FreePostCreate(BaseModel):
    title: str
    content: str
    is_anonymous: bool = False


class FreePostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class FreePostResponse(BaseModel):
    id: int
    title: str
    content: str
    image_path: str | None
    is_anonymous: bool
    author_id: int
    author_name: str          # 익명이면 "익명"
    created_at: datetime
    updated_at: datetime
    like_count: int
    comment_count: int

    model_config = {"from_attributes": True}


class FreePostListResponse(BaseModel):
    posts: list[FreePostResponse]
    total: int
    page: int
    size: int
    total_pages: int


class FreeCommentCreate(BaseModel):
    content: str
    is_anonymous: bool = False


class FreeCommentResponse(BaseModel):
    id: int
    content: str
    is_anonymous: bool
    author_id: int
    author_name: str          # 익명이면 "익명"
    post_id: int
    created_at: datetime
    like_count: int

    model_config = {"from_attributes": True}


class LikeResponse(BaseModel):
    liked: bool
    like_count: int
