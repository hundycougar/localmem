"""HTTP client for the mem.ai v2 API."""

from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://api.mem.ai/v2"


class MemClient:
    def __init__(self, api_key: str) -> None:
        self._http = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> MemClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ── Notes ────────────────────────────────────────────────

    def create_note(
        self,
        content: str,
        *,
        collection_ids: list[str] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"content": content}
        if collection_ids:
            body["collection_ids"] = collection_ids
        if created_at:
            body["created_at"] = created_at
        return self._post("/notes", body)

    def get_note(self, note_id: str) -> dict[str, Any]:
        return self._get(f"/notes/{note_id}")

    def update_note(self, note_id: str, content: str) -> dict[str, Any]:
        return self._patch(f"/notes/{note_id}", {"content": content})

    def delete_note(self, note_id: str) -> dict[str, Any]:
        return self._delete(f"/notes/{note_id}")

    def trash_note(self, note_id: str) -> dict[str, Any]:
        return self._post(f"/notes/{note_id}/trash", {})

    def list_notes(
        self,
        *,
        page: str | None = None,
        order: str = "updated_at",
        collection_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"order": order}
        if page:
            params["page"] = page
        if collection_id:
            params["collection_id"] = collection_id
        return self._get("/notes", params=params)

    def search_notes(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        return self._post("/notes/search", {"query": query, "limit": limit, "offset": offset})

    # ── Collections ──────────────────────────────────────────

    def list_collections(self, *, page: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {}
        if page:
            params["page"] = page
        return self._get("/collections", params=params)

    def create_collection(self, title: str, description: str = "") -> dict[str, Any]:
        body: dict[str, Any] = {"title": title}
        if description:
            body["description"] = description
        return self._post("/collections", body)

    # ── Mem It ───────────────────────────────────────────────

    def mem_it(
        self,
        input_text: str,
        *,
        instructions: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"input": input_text}
        if instructions:
            body["instructions"] = instructions
        return self._post("/mem-it", body)

    # ── HTTP helpers ─────────────────────────────────────────

    def _get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        r = self._http.get(path, params=params)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        r = self._http.post(path, json=body)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        r = self._http.patch(path, json=body)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str) -> dict[str, Any]:
        r = self._http.delete(path)
        r.raise_for_status()
        return r.json()
