from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

from app.database import get_db
from app.models.user import User
from app.models.recommendation import UserRecommendation
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.schemas.recommendation import RecommendResponse, UserRankingItem
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _user_response(user: User, db: Session) -> UserResponse:
    recommend_count = db.query(UserRecommendation).filter_by(recommended_id=user.id).count()
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        recommend_count=recommend_count,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=pwd_context.hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_response(user, db)


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    return {"access_token": create_access_token(user.id)}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _user_response(current_user, db)


@router.post("/users/{user_id}/recommend", response_model=RecommendResponse)
def toggle_recommend(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자신을 추천할 수 없습니다")
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    existing = db.query(UserRecommendation).filter_by(
        recommender_id=current_user.id, recommended_id=user_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        count = db.query(UserRecommendation).filter_by(recommended_id=user_id).count()
        return RecommendResponse(recommended=False, recommend_count=count)
    else:
        db.add(UserRecommendation(recommender_id=current_user.id, recommended_id=user_id))
        db.commit()
        count = db.query(UserRecommendation).filter_by(recommended_id=user_id).count()
        return RecommendResponse(recommended=True, recommend_count=count)


@router.get("/recommendations/ranking", response_model=list[UserRankingItem])
def get_ranking(db: Session = Depends(get_db)):
    users = db.query(User).all()
    ranking = [
        UserRankingItem(
            user_id=u.id,
            username=u.username,
            recommend_count=db.query(UserRecommendation).filter_by(recommended_id=u.id).count(),
        )
        for u in users
    ]
    ranking.sort(key=lambda x: x.recommend_count, reverse=True)
    return ranking[:10]