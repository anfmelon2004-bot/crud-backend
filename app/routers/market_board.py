from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.market_board import MarketPost, MarketPostLike
from app.models.purchase_request import PurchaseRequest
from app.schemas.market_board import MarketPostResponse, MarketPostListResponse
from app.schemas.free_board import LikeResponse
from app.schemas.purchase_request import PurchaseRequestCreate, PurchaseRequestResponse, PurchaseRequestStatusUpdate
from app.dependencies import get_current_user
from app.utils import save_image, delete_image

router = APIRouter(prefix="/market", tags=["장터게시판"])


def post_to_response(post: MarketPost) -> MarketPostResponse:
    return MarketPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        price=post.price,
        image_path=post.image_path,
        is_anonymous=post.is_anonymous,
        author_id=post.author_id,
        author_name="익명" if post.is_anonymous else post.author.username,
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=len(post.likes),
    )


def _req_to_response(req: PurchaseRequest) -> PurchaseRequestResponse:
    return PurchaseRequestResponse(
        id=req.id,
        post_id=req.post_id,
        buyer_id=req.buyer_id,
        buyer_name=req.buyer.username,
        message=req.message,
        status=req.status,
        created_at=req.created_at,
    )


@router.get("", response_model=MarketPostListResponse)
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(MarketPost).count()
    posts = (
        db.query(MarketPost)
        .order_by(MarketPost.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return MarketPostListResponse(
        posts=[post_to_response(p) for p in posts],
        total=total,
        page=page,
        size=size,
        total_pages=ceil(total / size) if total else 1,
    )


@router.get("/mine", response_model=MarketPostListResponse)
def list_my_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(MarketPost).filter(MarketPost.author_id == current_user.id).count()
    posts = (
        db.query(MarketPost)
        .filter(MarketPost.author_id == current_user.id)
        .order_by(MarketPost.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return MarketPostListResponse(
        posts=[post_to_response(p) for p in posts],
        total=total,
        page=page,
        size=size,
        total_pages=ceil(total / size) if total else 1,
    )


@router.get("/purchase-requests/sent", response_model=list[PurchaseRequestResponse])
def list_sent_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reqs = (
        db.query(PurchaseRequest)
        .filter(PurchaseRequest.buyer_id == current_user.id)
        .order_by(PurchaseRequest.created_at.desc())
        .all()
    )
    return [_req_to_response(r) for r in reqs]


@router.get("/purchase-requests/received", response_model=list[PurchaseRequestResponse])
def list_received_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    my_post_ids = [
        p.id for p in db.query(MarketPost).filter(MarketPost.author_id == current_user.id).all()
    ]
    reqs = (
        db.query(PurchaseRequest)
        .filter(PurchaseRequest.post_id.in_(my_post_ids))
        .order_by(PurchaseRequest.created_at.desc())
        .all()
    )
    return [_req_to_response(r) for r in reqs]


@router.patch("/purchase-requests/{request_id}", response_model=PurchaseRequestResponse)
def update_request_status(
    request_id: int,
    body: PurchaseRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="구매 요청을 찾을 수 없습니다")
    post = db.query(MarketPost).filter(MarketPost.id == req.post_id).first()
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글의 요청만 처리할 수 있습니다")
    if body.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="status는 accepted 또는 rejected여야 합니다")
    req.status = body.status
    db.commit()
    db.refresh(req)
    return _req_to_response(req)


@router.post("", response_model=MarketPostResponse, status_code=201)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    price: int = Form(...),
    is_anonymous: bool = Form(False),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_path = await save_image(image)
    post = MarketPost(
        title=title,
        content=content,
        price=price,
        is_anonymous=is_anonymous,
        image_path=image_path,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_to_response(post)


@router.get("/{post_id}", response_model=MarketPostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(MarketPost).filter(MarketPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return post_to_response(post)


@router.put("/{post_id}", response_model=MarketPostResponse)
async def update_post(
    post_id: int,
    title: str | None = Form(None),
    content: str | None = Form(None),
    price: int | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MarketPost).filter(MarketPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글만 수정할 수 있습니다")
    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
    if price is not None:
        post.price = price
    if image and image.filename:
        delete_image(post.image_path)
        post.image_path = await save_image(image)
    db.commit()
    db.refresh(post)
    return post_to_response(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MarketPost).filter(MarketPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글만 삭제할 수 있습니다")
    delete_image(post.image_path)
    db.delete(post)
    db.commit()


@router.post("/{post_id}/like", response_model=LikeResponse)
def toggle_post_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MarketPost).filter(MarketPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    existing = db.query(MarketPostLike).filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        db.refresh(post)
        return LikeResponse(liked=False, like_count=len(post.likes))
    else:
        db.add(MarketPostLike(user_id=current_user.id, post_id=post_id))
        db.commit()
        db.refresh(post)
        return LikeResponse(liked=True, like_count=len(post.likes))


@router.post("/{post_id}/purchase-requests", response_model=PurchaseRequestResponse, status_code=201)
def create_purchase_request(
    post_id: int,
    body: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MarketPost).filter(MarketPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    if post.author_id == current_user.id:
        raise HTTPException(status_code=400, detail="본인 게시글에는 구매 요청을 할 수 없습니다")
    if db.query(PurchaseRequest).filter_by(post_id=post_id, buyer_id=current_user.id).first():
        raise HTTPException(status_code=400, detail="이미 구매 요청을 보냈습니다")
    req = PurchaseRequest(post_id=post_id, buyer_id=current_user.id, message=body.message)
    db.add(req)
    db.commit()
    db.refresh(req)
    return _req_to_response(req)