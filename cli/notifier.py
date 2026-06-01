"""GameHub 推送通知模块 — 每日摘要 + 邮件推送"""
import asyncio
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

from api_client import fetch_steam_library, fetch_realtime_news

CACHE_DIR = Path.home() / ".gamehub"
CACHE_FILE = CACHE_DIR / "steam_library_cache.json"


def _load_cached_library() -> list:
    """加载本地缓存的 Steam 库"""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_library_cache(games: list):
    """保存 Steam 库到本地缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(games, ensure_ascii=False), encoding="utf-8")


def build_digest(games: list, news_items: list, profile_hours: int = 2686) -> str:
    """构建每日游戏资讯摘要"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Top 5 news
    news_section = ""
    for i, n in enumerate(news_items[:8], 1):
        game = n.get("_game_name", "Unknown")
        title = n.get("title", "")
        feed = n.get("feedlabel", n.get("feedname", ""))
        url = n.get("url", "")
        news_section += f"{i}. **[{game}]** {title}\n"
        if url:
            news_section += f"   {url}\n"

    # Top 5 games by playtime (from library context)
    sorted_games = sorted(games, key=lambda g: g.get("playtime_forever", 0), reverse=True)
    library_section = ""
    for g in sorted_games[:5]:
        name = g.get("name", "Unknown")
        hours = int(g.get("playtime_forever", 0) / 60)
        recent = g.get("playtime_2weeks", 0) / 60
        extra = f" (近两周 {recent:.1f}h)" if recent > 0 else ""
        library_section += f"- {name}: {hours}h{extra}\n"

    md = f"""# GameHub 每日游戏资讯

> {now} | Steam 库 {len(games)} 款 | 总时长 {profile_hours}h

---

## 今日热点

{news_section if news_section else '今日暂无新消息'}

---

## 你的 Top 5 游戏

{library_section}

---
*由 GameHub CLI 自动生成 | gamehub digest*
"""
    return md


def build_html_digest(md_content: str) -> str:
    """将 Markdown 摘要转为 HTML 邮件"""
    newline = "\n"
    body = md_content.replace(newline, "<br>")
    body = body.replace("## ", "<h2 style='color:#4fc3f7'>")
    body = body.replace("# ", "<h1 style='color:#4fc3f7'>")
    body = body.replace("- ", "&bull; ")
    body = body.replace("**", "<b>").replace("</b><b>", "")

    return f"""<html><body style="font-family:system-ui,sans-serif;background:#0f1117;color:#e1e1e1;padding:20px;max-width:700px;margin:auto">
<div style="background:#1a1c24;border-radius:12px;padding:24px">
{body}
</div>
<p style="color:#666;font-size:12px;text-align:center;margin-top:20px">GameHub Daily Digest · <a href='https://github.com/zhuobichen/GameHub' style='color:#4fc3f7'>GitHub</a></p>
</body></html>"""


def send_email(to_email: str, subject: str, html_body: str,
               smtp_host: str = "", smtp_port: int = 587,
               smtp_user: str = "", smtp_password: str = "",
               from_email: str = "") -> bool:
    """发送邮件推送"""
    if not smtp_host:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email or smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def generate_daily_digest(to_email: str = "",
                          smtp_host: str = "", smtp_port: int = 587,
                          smtp_user: str = "", smtp_password: str = "",
                          from_email: str = "") -> str:
    """生成每日摘要，可选邮件推送"""
    games = asyncio.run(fetch_steam_library())

    # Fallback to cache if API is down
    if not games:
        games = _load_cached_library()
        api_down = True
    else:
        _save_library_cache(games)
        api_down = False

    if not games:
        return "[错误] 无法获取 Steam 库且无本地缓存"

    total_h = int(sum(g.get("playtime_forever", 0) for g in games) / 60)
    news = asyncio.run(fetch_realtime_news(games, top_n=15))

    md = build_digest(games, news, total_h)

    if api_down:
        md += "\n\n> ⚠️ Steam API 暂时不可用，使用了本地缓存数据"

    if to_email and smtp_host:
        html = build_html_digest(md)
        success = send_email(to_email, f"GameHub Daily - {datetime.now().strftime('%m/%d')}", html,
                             smtp_host, smtp_port, smtp_user, smtp_password, from_email)
        if success:
            md += f"\n\n> 已推送到 {to_email}"

    return md
