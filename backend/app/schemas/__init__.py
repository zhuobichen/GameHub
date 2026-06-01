"""Pydantic schemas"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ===== Game =====
class GameBase(BaseModel):
    name: str
    steam_app_id: Optional[int] = None
    rawg_id: Optional[int] = None
    release_date: Optional[datetime] = None
    genres: Optional[list] = None
    tags: Optional[list] = None
    platforms: Optional[list] = None
    developers: Optional[list] = None
    publishers: Optional[list] = None
    cover_image: Optional[str] = None
    rating: Optional[float] = None
    price: Optional[float] = None
    final_price: Optional[float] = None
    discount_percent: int = 0
    current_players: int = 0


class GameOut(GameBase):
    id: int
    description: Optional[str] = None
    name_cn: Optional[str] = None
    metacritic_score: Optional[int] = None
    screenshots: Optional[list] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GameListOut(BaseModel):
    items: List[GameOut]
    total: int
    page: int
    page_size: int


# ===== User =====
class UserRegister(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    steam_id: Optional[str] = None
    preferences: Optional[dict] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserPreferences(BaseModel):
    genres: Optional[list] = None
    platforms: Optional[list] = None
    tags: Optional[list] = None
    excluded_tags: Optional[list] = None


# ===== Search =====
class SearchParams(BaseModel):
    q: str = ""
    genres: Optional[list] = None
    platforms: Optional[list] = None
    tags: Optional[list] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    released: Optional[bool] = None
    page: int = 1
    page_size: int = 20


class SearchOut(BaseModel):
    items: List[GameOut]
    total: int
    query: str
    page: int
    page_size: int


# ===== Recommendation =====
class RecommendationOut(BaseModel):
    games: List[GameOut]
    based_on: list = []
