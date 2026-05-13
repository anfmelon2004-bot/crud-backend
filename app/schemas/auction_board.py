from pydantic import BaseModel
from datetime import datetime


class AuctionPostCreate(BaseModel):
    title: str
    content: str
    course_name: str
    professor_name: str
    starting_price: int
    deadline: datetime
    is_anonymous: bool = False


class AuctionPostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class AuctionBidCreate(BaseModel):
    additional_amount: int  # 현재 최고가에서 추가할 금액


class AuctionBidResponse(BaseModel):
    id: int
    bid_amount: int
    bidder_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuctionPostResponse(BaseModel):
    id: int
    title: str
    content: str
    course_name: str
    professor_name: str
    starting_price: int
    current_price: int        # 현재 최고 입찰가
    deadline: datetime
    image_path: str | None
    is_anonymous: bool
    author_id: int
    author_name: str
    created_at: datetime
    is_ended: bool            # 마감 여부
    like_count: int
    bids: list[AuctionBidResponse]

    model_config = {"from_attributes": True}


class AuctionPostListResponse(BaseModel):
    posts: list[AuctionPostResponse]
    total: int
    page: int
    size: int
    total_pages: int
