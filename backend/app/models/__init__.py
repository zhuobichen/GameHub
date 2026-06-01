"""SQLAlchemy 数据模型"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from app.db.session import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_cn: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    steam_app_id: Mapped[Optional[int]] = mapped_column(BigInteger := Integer, unique=True)
    rawg_id: Mapped[Optional[int]]

    release_date: Mapped[Optional[datetime]]
    platforms: Mapped[Optional[dict]] = mapped_column(JSONB)    # ["pc","ps5"]
    genres: Mapped[Optional[dict]] = mapped_column(JSONB)       # ["RPG","Action"]
    tags: Mapped[Optional[dict]] = mapped_column(JSONB)         # ["open-world","multiplayer"]

    developers: Mapped[Optional[dict]] = mapped_column(JSONB)
    publishers: Mapped[Optional[dict]] = mapped_column(JSONB)

    cover_image: Mapped[Optional[str]] = mapped_column(String(500))
    screenshots: Mapped[Optional[dict]] = mapped_column(JSONB)

    rating: Mapped[Optional[float]] = mapped_column(Float)
    metacritic_score: Mapped[Optional[int]]

    price: Mapped[Optional[float]]
    discount_percent: Mapped[int] = mapped_column(default=0)
    final_price: Mapped[Optional[float]]

    current_players: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # full-text search
    search_vector = mapped_column(TSVECTOR)

    __table_args__ = (
        Index("ix_games_steam_app_id", "steam_app_id"),
        Index("ix_games_release_date", "release_date"),
        Index("ix_games_genres", "genres", postgresql_using="gin"),
        Index("ix_games_tags", "tags", postgresql_using="gin"),
        Index("ix_games_search", "search_vector", postgresql_using="gin"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    steam_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    steam_api_key: Mapped[Optional[str]] = mapped_column(String(100))

    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user_games: Mapped[List["UserGame"]] = relationship(back_populates="user")


class UserGame(Base):
    __tablename__ = "user_games"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))

    playtime_forever: Mapped[int] = mapped_column(default=0)
    playtime_2weeks: Mapped[int] = mapped_column(default=0)

    is_wishlisted: Mapped[bool] = mapped_column(default=False)
    is_following: Mapped[bool] = mapped_column(default=False)

    synced_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="user_games")
    game: Mapped["Game"] = relationship()

    __table_args__ = (
        Index("ix_user_games_user_id", "user_id"),
        Index("ix_user_games_game_id", "game_id"),
    )


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    query: Mapped[str] = mapped_column(String(255))
    result_count: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(50))  # 'release', 'price_drop', 'recommendation'
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    related_game_id: Mapped[Optional[int]] = mapped_column(ForeignKey("games.id"))
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
