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

from api_client import search_games, get_upcoming, get_recommendations, fetch_steam_library

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
def news():
    """AI news recommendations"""
    from ai_agent import recommend_news
    console.print("[cyan]AI searching for relevant news...[/cyan]")
    games = asyncio.run(fetch_steam_library())
    if not games:
        console.print("[red]Failed to fetch Steam library[/red]")
        return
    lib = [{"name": g.get("name", ""), "playtime_forever": g.get("playtime_forever", 0)} for g in games]
    response = recommend_news(lib, {})
    console.print(Panel(Markdown(response), title="News", border_style="magenta"))


if __name__ == "__main__":
    cli()
