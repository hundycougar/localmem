"""Minimal Flask web GUI for quick note access."""

from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from localmem.client import MemClient
from localmem.config import get_api_key


def create_app() -> Flask:
    app = Flask(__name__)

    def _client() -> MemClient:
        return MemClient(get_api_key())

    @app.route("/")
    def index():
        with _client() as c:
            data = c.list_notes()
        notes = data.get("notes", data.get("results", []))
        return render_template("index.html", notes=notes)

    @app.route("/note/<note_id>")
    def view_note(note_id: str):
        with _client() as c:
            note = c.get_note(note_id)
        return render_template("note.html", note=note)

    @app.route("/new", methods=["GET", "POST"])
    def new_note():
        if request.method == "POST":
            content = request.form.get("content", "").strip()
            if content:
                with _client() as c:
                    c.create_note(content)
                return redirect(url_for("index"))
        return render_template("new.html")

    @app.route("/search")
    def search():
        query = request.args.get("q", "").strip()
        notes = []
        if query:
            with _client() as c:
                data = c.search_notes(query)
            notes = data.get("notes", data.get("results", []))
        return render_template("search.html", query=query, notes=notes)

    return app
