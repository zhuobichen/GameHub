"""API v1 路由汇总"""
from fastapi import APIRouter
from app.api.v1 import games, search, users, auth, recommendations, notifications

v1_router = APIRouter()

v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
v1_router.include_router(users.router, prefix="/users", tags=["Users"])
v1_router.include_router(games.router, prefix="/games", tags=["Games"])
v1_router.include_router(search.router, prefix="/search", tags=["Search"])
v1_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
v1_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
