"""Celery Beat 定时任务配置"""
from celery.schedules import crontab
from app.core.celery_app import celery_app

celery_app.conf.beat_schedule = {
    # 每小时更新在线人数
    "sync-player-counts-hourly": {
        "task": "sync_player_counts",
        "schedule": 3600.0,
    },
    # 每天凌晨 2 点同步 Steam 游戏数据
    "sync-steam-games-daily": {
        "task": "sync_steam_games",
        "schedule": crontab(hour=2, minute=0),
    },
}
