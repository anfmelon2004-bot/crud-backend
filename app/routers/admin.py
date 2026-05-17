from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.free_board import FreePost
from app.models.market_board import MarketPost
from app.models.auction_board import AuctionPost
from app.models.review_board import ReviewPost
from app.models.report import Report, AdminLog
from app.schemas.admin import (
    AdminSummary, AdminUserResponse, AdminUserUpdate,
    AdminPostItem, ReportCreate, ReportResponse, ReportStatusUpdate, AdminLogResponse,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 없습니다")
    return current_user


def _log(db: Session, admin_id: int, action: str, target_type: str = None, target_id: int = None, detail: str = None):
    db.add(AdminLog(admin_id=admin_id, action=action, target_type=target_type, target_id=target_id, detail=detail))
    db.commit()


@router.get("/summary", response_model=AdminSummary)
def get_summary(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    return AdminSummary(
        user_count=db.query(User).count(),
        free_post_count=db.query(FreePost).count(),
        market_post_count=db.query(MarketPost).count(),
        auction_post_count=db.query(AuctionPost).count(),
        review_count=db.query(ReviewPost).count(),
        pending_report_count=db.query(Report).filter(Report.status == "pending").count(),
    )


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    if body.role is not None:
        user.role = body.role
    db.commit()
    db.refresh(user)
    _log(db, admin.id, "update_user_role", "user", user_id, f"role={body.role}")
    return user


@router.get("/posts", response_model=List[AdminPostItem])
def list_all_posts(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    posts = []
    for p in db.query(FreePost).all():
        posts.append(AdminPostItem(id=p.id, board="free", title=p.title,
            author_id=p.author_id, author_name=p.author.username, created_at=p.created_at))
    for p in db.query(MarketPost).all():
        posts.append(AdminPostItem(id=p.id, board="market", title=p.title,
            author_id=p.author_id, author_name=p.author.username, created_at=p.created_at))
    for p in db.query(AuctionPost).all():
        posts.append(AdminPostItem(id=p.id, board="auction", title=p.title,
            author_id=p.author_id, author_name=p.author.username, created_at=p.created_at))
    for p in db.query(ReviewPost).all():
        posts.append(AdminPostItem(id=p.id, board="reviews", title=p.title,
            author_id=p.author_id, author_name=p.author.username, created_at=p.created_at))
    posts.sort(key=lambda x: x.created_at, reverse=True)
    return posts


@router.delete("/posts/{board}/{post_id}", status_code=204)
def delete_post(
    board: str,
    post_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    model_map = {"free": FreePost, "market": MarketPost, "auction": AuctionPost, "reviews": ReviewPost}
    model = model_map.get(board)
    if not model:
        raise HTTPException(status_code=400, detail="잘못된 게시판입니다")
    post = db.query(model).filter(model.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    db.delete(post)
    db.commit()
    _log(db, admin.id, "delete_post", board, post_id)


@router.post("/reports", response_model=ReportResponse, status_code=201)
def create_report(
    body: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = Report(reporter_id=current_user.id, board=body.board, post_id=body.post_id, reason=body.reason)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=List[ReportResponse])
def list_reports(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.patch("/reports/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: int,
    body: ReportStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="신고를 찾을 수 없습니다")
    report.status = body.status
    db.commit()
    db.refresh(report)
    _log(db, admin.id, "update_report", "report", report_id, f"status={body.status}")
    return report


@router.get("/logs", response_model=List[AdminLogResponse])
def get_logs(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    logs = db.query(AdminLog).order_by(AdminLog.created_at.desc()).limit(100).all()
    return [
        AdminLogResponse(
            id=log.id,
            admin_id=log.admin_id,
            admin_name=log.admin.username,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            detail=log.detail,
            created_at=log.created_at,
        )
        for log in logs
    ]