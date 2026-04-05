# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

localmem is a local Python client for [mem.ai](https://mem.ai) — a CLI + web GUI for managing notes via the mem.ai v2 API (`https://api.mem.ai/v2`).

## Commands

```bash
# Install (editable, for development)
pip install -e .

# Run CLI
localmem --help
localmem ls                    # list notes
localmem get <note_id>         # read a note
localmem new "# Title\nBody"   # create a note
localmem edit <note_id>        # edit in $EDITOR
localmem search "query"        # search notes
localmem rm <note_id>          # trash a note
localmem mem-it "raw content"  # AI ingestion
localmem collections ls        # list collections
localmem config set-key KEY    # save API key

# Start web GUI
localmem serve                 # http://127.0.0.1:8080
localmem serve -p 3000         # custom port
```

## Architecture

- **`localmem/config.py`** — API key resolution: checks `MEM_API_KEY` env var, then `~/.config/localmem/config`.
- **`localmem/client.py`** — `MemClient` class wrapping the mem.ai v2 REST API with httpx. All API methods return parsed JSON dicts. Used as a context manager.
- **`localmem/cli.py`** — Click CLI. Each subcommand instantiates a `MemClient`, calls the relevant method, and formats output with Rich.
- **`localmem/web.py`** — Flask app factory (`create_app()`). Launched via `localmem serve`. Templates in `localmem/templates/`.

The CLI and web GUI are independent interfaces that both go through `MemClient`. The web app is intentionally minimal — a quick-capture tool, not a full note editor.

## API Key

Must be set before use. Either:
- `export MEM_API_KEY=...`
- `localmem config set-key YOUR_KEY` (writes to `~/.config/localmem/config`)

## mem.ai API Notes

- Notes use markdown; first line of content becomes the title.
- `list_notes` and `list_collections` use cursor-based pagination (`next_page` field).
- `search_notes` uses offset pagination with `limit` (max 50).
- `trash_note` is recoverable; `delete_note` is permanent.
- `mem_it` is async — returns a `request_id`, processing happens server-side.
