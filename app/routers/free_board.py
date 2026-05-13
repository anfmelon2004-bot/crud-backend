from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.free_board import FreePost, FreeComment, FreePostLike, FreeCommentLike
from app.schemas.free_board import (
    FreePostResponse, FreePostListResponse,
    FreeCommentCreate, FreeCommentResponse, LikeResponse,
)
from app.dependencies import get_current_user
from app.utils import save_image, delete_image

router = APIRouter(prefix="/free-board", tags=["자유게시판"])


def resolve_name(is_anonymous: bool, username: str) -> str:
    return "익명" if is_anonymous else username


def post_to_response(post: FreePost) -> FreePostResponse:
    return FreePostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        image_path=post.image_path,
        is_anonymous=post.is_anonymous,
        author_id=post.author_id,
        author_name=resolve_name(post.is_anonymous, post.author.username),
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=len(post.likes),
        comment_count=len(post.comments),
    )


# ── 게시글 ──────────────────────────────────────────────

@router.get("", response_model=FreePostListResponse)
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(FreePost).count()
    posts = (
        db.query(FreePost)
        .order_by(FreePost.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return FreePostListResponse(
        posts=[post_to_response(p) for p in posts],
        total=total,
        page=page,
        size=size,
        total_pages=ceil(total / size) if total else 1,
    )


@router.post("", response_model=FreePostResponse, status_code=201)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    is_anonymous: bool = Form(False),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_path = await save_image(image)
    post = FreePost(
        title=title,
        content=content,
        is_anonymous=is_anonymous,
        image_path=image_path,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_to_response(post)


@router.get("/{post_id}", response_model=FreePostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(FreePost).filter(FreePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return post_to_response(post)


@router.put("/{post_id}", response_model=FreePostResponse)
async def update_post(
    post_id: int,
    title: str | None = Form(None),
    content: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(FreePost).filter(FreePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글만 수정할 수 있습니다")

    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
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
    post = db.query(FreePost).filter(FreePost.id == post_id).first()
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
    post = db.query(FreePost).filter(FreePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    existing = db.query(FreePostLike).filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        db.refresh(post)
        return LikeResponse(liked=False, like_count=len(post.likes))
    else:
        db.add(FreePostLike(user_id=current_user.id, post_id=post_id))
        db.commit()
        db.refresh(post)
        return LikeResponse(liked=True, like_count=len(post.likes))


# ── 댓글 ──────────────────────────────────────────────

@router.get("/{post_id}/comments", response_model=list[FreeCommentResponse])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(FreePost).filter(FreePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return [
        FreeCommentResponse(
            id=c.id,
            content=c.content,
            is_anonymous=c.is_anonymous,
            author_id=c.author_id,
            author_name=resolve_name(c.is_anonymous, c.author.username),
            post_id=c.post_id,
            created_at=c.created_at,
            like_count=len(c.likes),
        )
        for c in post.comments
    ]


@router.post("/{post_id}/comments", response_model=FreeCommentResponse, status_code=201)
def create_comment(
    post_id: int,
    body: FreeCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(FreePost).filter(FreePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    comment = FreeComment(
        content=body.content,
        is_anonymous=body.is_anonymous,
        author_id=current_user.id,
        post_id=post_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return FreeCommentResponse(
        id=comment.id,
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        author_id=comment.author_id,
        author_name=resolve_name(comment.is_anonymous, current_user.username),
        post_id=comment.post_id,
        created_at=comment.created_at,
        like_count=0,
    )


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(FreeComment).filter(FreeComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 삭제할 수 있습니다")

    db.delete(comment)
    db.commit()


@router.post("/comments/{comment_id}/like", response_model=LikeResponse)
def toggle_comment_like(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(FreeComment).filter(FreeComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")

    existing = db.query(FreeCommentLike).filter_by(user_id=current_user.id, comment_id=comment_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return LikeResponse(liked=False, like_count=len(comment.likes) - 1)
    else:
        db.add(FreeCommentLike(user_id=current_user.id, comment_id=comment_id))
        db.commit()
        return LikeResponse(liked=True, like_count=len(comment.likes) + 1)
