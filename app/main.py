from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.models import user, free_board, market_board, auction_board, review_board, recommendation, purchase_request, report  # noqa: F401
from app.routers import auth, free_board as free, market_board as market, auction_board as auction, review_board as review, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRUD 게시판 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(free.router)
app.include_router(market.router)
app.include_router(auction.router)
app.include_router(review.router)
app.include_router(admin.router)


@app.get("/")
def health_check():
    return {"status": "ok"}