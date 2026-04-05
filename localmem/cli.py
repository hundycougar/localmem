"""CLI interface for localmem."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from localmem.client import MemClient
from localmem.config import get_api_key, set_api_key

console = Console()


def _client() -> MemClient:
    return MemClient(get_api_key())


def _note_title(content: str, max_len: int = 60) -> str:
    """Extract first line as title, truncated."""
    first = content.split("\n", 1)[0].lstrip("# ").strip()
    if len(first) > max_len:
        return first[: max_len - 1] + "…"
    return first


@click.group()
def cli() -> None:
    """localmem — local client for mem.ai"""


# ── Config ───────────────────────────────────────────────────

@cli.group()
def config() -> None:
    """Manage configuration."""


@config.command("set-key")
@click.argument("key")
def config_set_key(key: str) -> None:
    """Save your mem.ai API key."""
    set_api_key(key)
    console.print("[green]API key saved.[/green]")


# ── Notes ────────────────────────────────────────────────────

@cli.command("ls")
@click.option("--collection", "-c", default=None, help="Filter by collection ID.")
@click.option("--page", "-p", default=None, help="Pagination cursor.")
def list_notes(collection: str | None, page: str | None) -> None:
    """List recent notes."""
    with _client() as c:
        data = c.list_notes(collection_id=collection, page=page)

    notes = data.get("notes", data.get("results", []))
    if not notes:
        console.print("[dim]No notes found.[/dim]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Title")
    table.add_column("Updated", style="cyan")

    for n in notes:
        table.add_row(
            n["id"],
            _note_title(n.get("content", "")),
            n.get("updated_at", "")[:10],
        )
    console.print(table)

    next_page = data.get("next_page")
    if next_page:
        console.print(f"\n[dim]Next page: --page {next_page}[/dim]")


@cli.command("get")
@click.argument("note_id")
def get_note(note_id: str) -> None:
    """Read a note by ID."""
    with _client() as c:
        note = c.get_note(note_id)
    console.print(Markdown(note["content"]))


@cli.command("new")
@click.argument("content", required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="Read content from file.")
@click.option("--collection", "-c", multiple=True, help="Collection ID to link.")
def new_note(content: str | None, file: str | None, collection: tuple[str, ...]) -> None:
    """Create a new note. Pass content as argument, --file, or pipe via stdin."""
    if file:
        with open(file) as f:
            content = f.read()
    elif content is None:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            content = click.edit()
            if content is None:
                raise SystemExit("Aborted.")

    with _client() as c:
        note = c.create_note(
            content,
            collection_ids=list(collection) if collection else None,
        )
    console.print(f"[green]Created:[/green] {note['id']}")


@cli.command("edit")
@click.argument("note_id")
def edit_note(note_id: str) -> None:
    """Edit a note in your $EDITOR."""
    with _client() as c:
        note = c.get_note(note_id)
        edited = click.edit(note["content"])
        if edited is None or edited == note["content"]:
            console.print("[dim]No changes.[/dim]")
            return
        c.update_note(note_id, edited)
    console.print(f"[green]Updated:[/green] {note_id}")


@cli.command("rm")
@click.argument("note_id")
@click.option("--permanent", is_flag=True, help="Permanently delete instead of trashing.")
def remove_note(note_id: str, permanent: bool) -> None:
    """Trash (or permanently delete) a note."""
    with _client() as c:
        if permanent:
            c.delete_note(note_id)
            console.print(f"[red]Deleted:[/red] {note_id}")
        else:
            c.trash_note(note_id)
            console.print(f"[yellow]Trashed:[/yellow] {note_id}")


@cli.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Max results.")
def search_notes(query: str, limit: int) -> None:
    """Search notes."""
    with _client() as c:
        data = c.search_notes(query, limit=limit)

    notes = data.get("notes", data.get("results", []))
    if not notes:
        console.print("[dim]No results.[/dim]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Title")

    for n in notes:
        table.add_row(n["id"], _note_title(n.get("content", n.get("snippet", ""))))
    console.print(table)


# ── Mem It ───────────────────────────────────────────────────

@cli.command("mem-it")
@click.argument("input_text", required=False)
@click.option("--instructions", "-i", default=None, help="Processing instructions.")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read input from file.")
def mem_it(input_text: str | None, instructions: str | None, file: str | None) -> None:
    """Send content to Mem It for AI processing."""
    if file:
        with open(file) as f:
            input_text = f.read()
    elif input_text is None:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
        else:
            raise SystemExit("Provide input as argument, --file, or pipe via stdin.")

    with _client() as c:
        result = c.mem_it(input_text, instructions=instructions)
    console.print(f"[green]Submitted:[/green] request_id={result.get('request_id', 'n/a')}")


# ── Collections ──────────────────────────────────────────────

@cli.group("collections")
def collections_group() -> None:
    """Manage collections."""


@collections_group.command("ls")
def list_collections() -> None:
    """List collections."""
    with _client() as c:
        data = c.list_collections()

    cols = data.get("collections", data.get("results", []))
    if not cols:
        console.print("[dim]No collections.[/dim]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Title")

    for col in cols:
        table.add_row(col["id"], col.get("title", ""))
    console.print(table)


# ── Web server ───────────────────────────────────────────────

@cli.command("serve")
@click.option("--port", "-p", default=8080, help="Port to listen on.")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to.")
def serve(port: int, host: str) -> None:
    """Start the web GUI."""
    from localmem.web import create_app

    app = create_app()
    console.print(f"[green]Serving on http://{host}:{port}[/green]")
    app.run(host=host, port=port, debug=False)
