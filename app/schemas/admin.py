from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdminSummary(BaseModel):
    user_count: int
    free_post_count: int
    market_post_count: int
    auction_post_count: int
    review_count: int
    pending_report_count: int


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None


class AdminPostItem(BaseModel):
    id: int
    board: str
    title: str
    author_id: int
    author_name: str
    created_at: datetime


class ReportCreate(BaseModel):
    board: str
    post_id: int
    reason: str


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    board: str
    post_id: int
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportStatusUpdate(BaseModel):
    status: str


class AdminLogResponse(BaseModel):
    id: int
    admin_id: int
    admin_name: str
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    detail: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}