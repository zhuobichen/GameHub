"""Pydantic schemas"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PlatformType(str, Enum):
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    TWITTER = "twitter"
    HACKER_NEWS = "hacker_news"
    TIKTOK = "tiktok"
    TWITCH = "twitch"
    XIAOHEIHE = "xiaoheihe"
    NGA = "nga"
    TAPTAP = "taptap"
    BILIBILI = "bilibili"


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


# ===== Social Content =====
class SocialContentBase(BaseModel):
    platform: PlatformType
    content_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    author_avatar: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    score: float = 0.0
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    published_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class SocialContentOut(SocialContentBase):
    id: int
    game_id: Optional[int] = None
    fetched_at: datetime

    class Config:
        from_attributes = True


class SocialContentListOut(BaseModel):
    items: List[SocialContentOut]
    total: int
    page: int
    page_size: int


class AggregatedInsightOut(BaseModel):
    game_id: Optional[int] = None
    game_name: Optional[str] = None
    total_mentions: int
    platform_breakdown: dict
    top_posts: List[SocialContentOut]
    sentiment_score: Optional[float] = None
    trending_score: float
    last_updated: datetime


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
