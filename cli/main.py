#!/usr/bin/env python3
"""GameHub CLI -- game search + AI recommendations"""

import asyncio
import sys
import io
import click
from rich.console import Console

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from api_client import search_games, get_upcoming, get_recommendations, fetch_steam_library, fetch_realtime_news

console = Console()


def _build_library_table(games: list, limit: int = 30) -> Table:
    table = Table(title="Steam Library", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Game", style="white")
    table.add_column("Hours", justify="right", style="yellow")
    table.add_column("2weeks", justify="right", style="green")

    sorted_games = sorted(games, key=lambda g: g.get("playtime_forever", 0), reverse=True)
    for i, g in enumerate(sorted_games[:limit], 1):
        table.add_row(
            str(i),
            g.get("name", "Unknown")[:40],
            str(int(g.get("playtime_forever", 0) / 60)),
            f"{g.get('playtime_2weeks', 0) / 60:.1f}" if g.get("playtime_2weeks", 0) > 0 else "-",
        )

    total = len(games)
    total_h = sum(g.get("playtime_forever", 0) for g in games) / 60
    table.caption = f"{total} games / {int(total_h)}h total"
    return table


def _build_game_table(title: str, games: list) -> Table:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Game", style="white", max_width=30)
    table.add_column("Rating", justify="right", style="yellow")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Release", style="dim")

    for g in games:
        price = f"Y{g.get('final_price', '?')}" if g.get("final_price") else "-"
        table.add_row(
            g.get("name", "Unknown")[:30],
            f"{g.get('rating', '-')}",
            price,
            g.get("release_date", "-")[:10] if g.get("release_date") else "TBA",
        )
    return table


@click.group()
def cli():
    """GameHub - Game search engine + AI recommendations"""
    pass


@cli.command()
@click.argument("query")
def search(query):
    """Search games"""
    async def _run():
        result = await search_games(query)
        items = result.get("items", [])
        if not items:
            console.print("[yellow]No results[/yellow]")
            return
        table = _build_game_table(f"Search: {query} ({result.get('total', 0)} results)", items)
        console.print(table)
    asyncio.run(_run())


@cli.command()
def library():
    """View Steam library"""
    console.print("[cyan]Fetching Steam library...[/cyan]")
    games = asyncio.run(fetch_steam_library())
    if not games:
        console.print("[red]Failed, check STEAM_API_KEY and STEAM_ID[/red]")
        return
    table = _build_library_table(games)
    console.print(table)
    total_h = sum(g.get("playtime_forever", 0) for g in games) / 60
    recent_h = sum(g.get("playtime_2weeks", 0) for g in games) / 60
    console.print(f"[dim]{int(total_h)}h total | {recent_h:.1f}h recent | {len(games)} games[/dim]")


@cli.command()
def upcoming():
    """View upcoming releases"""
    result = asyncio.run(get_upcoming())
    items = result.get("items", [])
    if not items:
        console.print("[yellow]No data[/yellow]")
        return
    table = _build_game_table(f"Upcoming ({len(items)} games)", items)
    console.print(table)


@cli.command()
def recommend():
    """Get recommendations"""
    result = asyncio.run(get_recommendations())
    items = result.get("games", [])
    based_on = result.get("based_on", [])
    if not items:
        console.print("[yellow]No recommendations. Sync Steam library first.[/yellow]")
        return
    table = _build_game_table(f"Recommended (based on: {', '.join(based_on)})", items)
    console.print(table)


@cli.command()
@click.argument("question")
def ai(question):
    """AI recommendation (requires ANTHROPIC_API_KEY)"""
    from ai_agent import ask
    console.print("[cyan]AI thinking...[/cyan]")
    games = asyncio.run(fetch_steam_library())
    if not games:
        console.print("[red]Failed to fetch Steam library[/red]")
        return
    lib = [{"name": g.get("name", ""), "playtime_forever": g.get("playtime_forever", 0)} for g in games]
    response = ask(lib, {}, question)
    console.print(Panel(Markdown(response), title="AI Recommendation", border_style="magenta"))


@cli.command()
def analyze():
    """AI taste analysis"""
    from ai_agent import analyze_taste
    console.print("[cyan]Analyzing your gaming taste...[/cyan]")
    games = asyncio.run(fetch_steam_library())
    if not games:
        console.print("[red]Failed to fetch Steam library[/red]")
        return
    lib = [{"name": g.get("name", ""), "playtime_forever": g.get("playtime_forever", 0)} for g in games]
    response = analyze_taste(lib, {})
    console.print(Panel(Markdown(response), title="Taste Analysis", border_style="magenta"))


@cli.command()
def profile():
    """Show your gaming profile (auto-generated from Steam)"""
    from collections import Counter
    console.print("[cyan]Building your gamer profile...[/cyan]")
    games = asyncio.run(fetch_steam_library())
    if not games:
        console.print("[red]Failed to fetch Steam library[/red]")
        return

    import httpx
    games.sort(key=lambda g: g.get("playtime_forever", 0), reverse=True)

    total = len(games)
    total_h = sum(g["playtime_forever"] for g in games) / 60
    recent_h = sum(g.get("playtime_2weeks", 0) for g in games) / 60
    avg_h = total_h / total if total else 0

    # Fetch genres for top games
    all_genres = Counter()
    top_games = []

    async def _fetch():
        async with httpx.AsyncClient(timeout=30) as c:
            for g in games[:20]:
                try:
                    r = await c.get("https://store.steampowered.com/api/appdetails",
                        params={"appids": g["appid"], "l": "schinese", "cc": "CN"})
                    d = r.json().get(str(g["appid"]), {})
                    if d.get("success"):
                        data = d["data"]
                        hours = g["playtime_forever"] / 60
                        genres = [x["description"] for x in data.get("genres", [])]
                        for genre in genres:
                            all_genres[genre] += hours
                        top_games.append({"name": data["name"], "hours": int(hours), "genres": genres})
                except:
                    pass

    asyncio.run(_fetch())

    # Build profile panels
    from rich.panel import Panel
    from rich.table import Table

    # Basic stats
    console.print(Panel(
        f"[bold]Gamer Profile[/bold]\n"
        f"Games: {total} | Total: {int(total_h)}h | Recent: {recent_h:.1f}h | Avg: {avg_h:.1f}h/game",
        border_style="cyan"))

    # Genre affinity (by playtime)
    genre_table = Table(title="Genre Affinity (weighted by playtime)", show_header=True)
    genre_table.add_column("Genre", style="green")
    genre_table.add_column("Hours", justify="right", style="yellow")
    genre_table.add_column("Bar", style="cyan")
    max_h = all_genres.most_common(1)[0][1] if all_genres else 1
    for genre, hours in all_genres.most_common(8):
        bar = "=" * int(hours / max_h * 20)
        genre_table.add_row(genre, f"{int(hours)}h", bar)
    console.print(genre_table)

    # Play pattern
    ranges = {"0-10h": 0, "10-30h": 0, "30-60h": 0, "60-100h": 0, "100h+": 0}
    for g in games:
        h = g["playtime_forever"] / 60
        if h < 10: ranges["0-10h"] += 1
        elif h < 30: ranges["10-30h"] += 1
        elif h < 60: ranges["30-60h"] += 1
        elif h < 100: ranges["60-100h"] += 1
        else: ranges["100h+"] += 1

    pattern_text = "  ".join(f"[bold]{v}[/bold] {k}" for k, v in ranges.items())
    console.print(Panel(pattern_text, title="Play Time Distribution", border_style="yellow"))

    # Top games
    game_table = Table(title="Top Games", show_header=True)
    game_table.add_column("#", style="dim", width=3)
    game_table.add_column("Game", style="white")
    game_table.add_column("Hours", justify="right", style="yellow")
    game_table.add_column("Genres", style="green")
    for i, g in enumerate(top_games[:10], 1):
        game_table.add_row(str(i), g["name"][:30], str(g["hours"]), ", ".join(g["genres"][:3]))
    console.print(game_table)


@cli.command()
def digest():
    """Generate daily news digest (based on your profile)"""
    from notifier import generate_daily_digest
    console.print("[cyan]Generating daily digest...[/cyan]")
    md = generate_daily_digest()
    console.print(Markdown(md))

    # Save to file
    from datetime import datetime
    import os
    save_dir = os.path.expanduser("~/.gamehub")
    os.makedirs(save_dir, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    save_path = os.path.join(save_dir, f"digest-{today}.md")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(md)
    console.print(f"[dim]Saved to {save_path}[/dim]")


@cli.command()
def push():
    """Push daily digest via email"""
    from notifier import generate_daily_digest
    from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_TO
    if not EMAIL_TO:
        console.print("[red]请设置 GAMEHUB_EMAIL_TO 环境变量[/red]")
        console.print("[dim]例如: set GAMEHUB_EMAIL_TO=your@email.com[/dim]")
        return
    console.print(f"[cyan]Pushing digest to {EMAIL_TO}...[/cyan]")
    result = generate_daily_digest(
        to_email=EMAIL_TO,
        smtp_host=EMAIL_HOST,
        smtp_port=EMAIL_PORT,
        smtp_user=EMAIL_USER,
        smtp_password=EMAIL_PASSWORD,
        from_email=EMAIL_USER,
    )
    if "已推送到" in result:
        console.print(f"[green]Digest pushed to {EMAIL_TO}[/green]")
    else:
        console.print("[yellow]Digest generated but email not sent (check SMTP config)[/yellow]")


@cli.command()
def news():
    """Real-time Steam news from your library"""
    console.print("[cyan]Fetching real-time Steam news...[/cyan]")
    games = asyncio.run(fetch_steam_library())
    if not games:
        console.print("[red]Failed to fetch Steam library[/red]")
        return

    news_items = asyncio.run(fetch_realtime_news(games, top_n=15))

    if not news_items:
        console.print("[yellow]No news found[/yellow]")
        return

    # Build table
    table = Table(title="Steam News (Real-time from your library)", show_header=True, header_style="bold cyan")
    table.add_column("Date", style="dim", width=10)
    table.add_column("Game", style="green", max_width=20)
    table.add_column("Title", style="white", max_width=50)
    table.add_column("Feed", style="dim", max_width=12)

    from datetime import datetime
    for n in news_items[:25]:
        dt = datetime.fromtimestamp(n.get("date", 0))
        date_str = dt.strftime("%m-%d %H:%M")
        table.add_row(
            date_str,
            n.get("_game_name", "Unknown")[:20],
            n.get("title", "")[:50],
            n.get("feedlabel", n.get("feedname", ""))[:12],
        )

    console.print(table)

    # AI summary of top news
    from ai_agent import ask
    console.print("\n[cyan]AI summarizing top news...[/cyan]")
    headlines = "\n".join(
        f"- [{n['_game_name']}] {n['title']} ({n.get('feedlabel', '')})"
        for n in news_items[:15]
    )
    summary = ask(
        [{"name": n["_game_name"], "playtime_forever": n.get("_playtime_h", 0) * 60} for n in news_items[:10]],
        {},
        f"以下是 Steam 最近的游戏新闻头条，请用3-5句话总结最重要的动态：\n\n{headlines}",
    )
    console.print(Panel(Markdown(summary), title="AI Summary", border_style="magenta"))


if __name__ == "__main__":
    cli()
