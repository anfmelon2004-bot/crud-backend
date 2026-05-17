from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PurchaseRequestCreate(BaseModel):
    message: Optional[str] = None


class PurchaseRequestResponse(BaseModel):
    id: int
    post_id: int
    buyer_id: int
    buyer_name: str
    message: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseRequestStatusUpdate(BaseModel):
    status: str