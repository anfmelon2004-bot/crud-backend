from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.review_board import ReviewPost, ReviewPostLike
from app.schemas.review_board import (
    ReviewPostCreate, ReviewPostUpdate,
    ReviewPostResponse, ReviewPostListResponse, LikeResponse,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/reviews", tags=["강의평게시판"])


def post_to_response(post: ReviewPost) -> ReviewPostResponse:
    return ReviewPostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        course_name=post.course_name,
        professor_name=post.professor_name,
        assignment_level=post.assignment_level,
        team_project_load=post.team_project_load,
        grading_style=post.grading_style,
        rating=post.rating,
        year=post.year,
        semester=post.semester,
        author_id=post.author_id,
        author_name=post.author.username,
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=len(post.likes),
    )


@router.get("", response_model=ReviewPostListResponse)
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="강의명 또는 교수명 통합 검색"),
    course_name: str | None = Query(None, description="강의명으로 필터"),
    professor_name: str | None = Query(None, description="교수명으로 필터"),
    db: Session = Depends(get_db),
):
    query = db.query(ReviewPost)

    if search:
        query = query.filter(
            ReviewPost.course_name.contains(search) |
            ReviewPost.professor_name.contains(search)
        )
    if course_name:
        query = query.filter(ReviewPost.course_name.contains(course_name))
    if professor_name:
        query = query.filter(ReviewPost.professor_name.contains(professor_name))

    total = query.count()
    posts = query.order_by(ReviewPost.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return ReviewPostListResponse(
        posts=[post_to_response(p) for p in posts],
        total=total,
        page=page,
        size=size,
        total_pages=ceil(total / size) if total else 1,
    )


@router.post("", response_model=ReviewPostResponse, status_code=201)
def create_post(
    body: ReviewPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = ReviewPost(
        title=body.title,
        content=body.content,
        course_name=body.course_name,
        professor_name=body.professor_name,
        assignment_level=body.assignment_level,
        team_project_load=body.team_project_load,
        grading_style=body.grading_style,
        rating=body.rating,
        year=body.year,
        semester=body.semester,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_to_response(post)


@router.get("/{post_id}", response_model=ReviewPostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ReviewPost).filter(ReviewPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return post_to_response(post)


@router.put("/{post_id}", response_model=ReviewPostResponse)
def update_post(
    post_id: int,
    body: ReviewPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(ReviewPost).filter(ReviewPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글만 수정할 수 있습니다")

    if body.title is not None:
        post.title = body.title
    if body.content is not None:
        post.content = body.content
    if body.assignment_level is not None:
        post.assignment_level = body.assignment_level

    db.commit()
    db.refresh(post)
    return post_to_response(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(ReviewPost).filter(ReviewPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글만 삭제할 수 있습니다")

    db.delete(post)
    db.commit()


@router.post("/{post_id}/like", response_model=LikeResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(ReviewPost).filter(ReviewPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    existing = db.query(ReviewPostLike).filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return LikeResponse(liked=False, like_count=len(post.likes) - 1)
    else:
        db.add(ReviewPostLike(user_id=current_user.id, post_id=post_id))
        db.commit()
        return LikeResponse(liked=True, like_count=len(post.likes) + 1)
