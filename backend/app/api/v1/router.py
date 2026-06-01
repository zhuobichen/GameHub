"""API v1 路由汇总"""
from fastapi import APIRouter
from app.api.v1 import games, search, users, auth, recommendations, notifications, social, profile

v1_router = APIRouter()

v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
v1_router.include_router(users.router, prefix="/users", tags=["Users"])
v1_router.include_router(games.router, prefix="/games", tags=["Games"])
v1_router.include_router(search.router, prefix="/search", tags=["Search"])
v1_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
v1_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
v1_router.include_router(social.router, prefix="/social", tags=["Social"])
v1_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
