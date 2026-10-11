#!/usr/bin/env python3
from __future__ import annotations

"""Resolve a WhatsApp JID to its relationship and Chroma collection."""

import json
from pathlib import Path


def resolve_relationship(
    jid: str,
    map_path: str = "config/relationship_map.json",
) -> tuple[str, str | None]:
    """Resolve a WhatsApp number or group JID."""

    if not isinstance(jid, str) or not jid.strip():
        return ("unknown", "history_unknown")

    normalized = jid.strip()

    # Group chats do not use an individual relationship collection.
    if normalized.endswith("@g.us"):
        return ("group", None)

    number = normalized.split("@", 1)[0]

    if not number:
        return ("unknown", "history_unknown")

    relationship_map_path = Path(map_path)

    if relationship_map_path.exists():
        with relationship_map_path.open(
            "r", encoding="utf-8"
        ) as map_file:
            relationship_map = json.load(map_file)
    else:
        relationship_map = {}

    if not isinstance(relationship_map, dict):
        relationship_map = {}

    relationship = relationship_map.get(
        number,
        relationship_map.get("_default", "unknown"),
    )

    if relationship == "group":
        return ("group", None)

    collection_name = f"history_{relationship}"
    return relationship, collection_name