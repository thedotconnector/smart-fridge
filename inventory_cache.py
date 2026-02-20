"""In-memory inventory cache backed by JSON on disk."""

import json
import os
import uuid
from datetime import datetime

from food_mapping import resolve_food

CACHE_PATH = "/tmp/fridge_inventory_cache.json"

_cache = {
    "items": [],
    "sections": {
        "fresh": {"last_updated": None, "photo_timestamp": None},
        "top": {"last_updated": None, "photo_timestamp": None},
        "door": {"last_updated": None, "photo_timestamp": None},
    },
    "history": [],  # previously seen items for suggestions
}


def _load_from_disk():
    """Load cache from disk if it exists."""
    global _cache
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f:
                _cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass


def _save_to_disk():
    """Persist cache to disk."""
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(_cache, f, indent=2)
    except IOError:
        pass


# Load on import
_load_from_disk()


def get_cached_inventory():
    """Return cached inventory without any Dropbox/Claude calls."""
    return {
        "items": _cache["items"],
        "sections": _cache["sections"],
        "last_updated": _cache["sections"].get("fresh", {}).get("last_updated"),
    }


def rebuild_section(section, items_raw, photo_timestamp=None):
    """Rebuild a section's items from raw analysis results.

    Args:
        section: 'fresh', 'top', or 'door'
        items_raw: list of {'name': str, 'quantity': int} from structured analysis
        photo_timestamp: ISO string of when the photo was taken
    """
    # Move current items from this section to history
    current_section_items = [i for i in _cache["items"] if i["shelf"] == section]
    for item in current_section_items:
        if item["name"] not in [h["name"] for h in _cache.get("history", [])]:
            _cache.setdefault("history", []).append({
                "name": item["name"],
                "emoji": item["emoji"],
                "category": item["category"],
                "last_seen": datetime.utcnow().isoformat(),
            })

    # Remove old items from this section
    _cache["items"] = [i for i in _cache["items"] if i["shelf"] != section]

    # Add new items
    now = datetime.utcnow().isoformat()
    for raw in items_raw:
        canonical, info = resolve_food(raw["name"])
        _cache["items"].append({
            "id": str(uuid.uuid4()),
            "name": canonical,
            "emoji": info["emoji"],
            "category": info["category"],
            "shelf": section,
            "quantity": raw.get("quantity", 1),
            "source": "photo",
            "added_at": now,
        })

    # Update section metadata
    _cache["sections"][section] = {
        "last_updated": now,
        "photo_timestamp": photo_timestamp,
    }

    _save_to_disk()


def add_manual_item(name, shelf="fresh", quantity=1):
    """Manually add an item to the inventory."""
    canonical, info = resolve_food(name)
    item = {
        "id": str(uuid.uuid4()),
        "name": canonical,
        "emoji": info["emoji"],
        "category": info["category"],
        "shelf": shelf,
        "quantity": quantity,
        "source": "manual",
        "added_at": datetime.utcnow().isoformat(),
    }
    _cache["items"].append(item)
    _save_to_disk()
    return item


def remove_item(item_id):
    """Remove an item by ID. Returns True if found and removed."""
    for i, item in enumerate(_cache["items"]):
        if item["id"] == item_id:
            removed = _cache["items"].pop(i)
            # Add to history
            if removed["name"] not in [h["name"] for h in _cache.get("history", [])]:
                _cache.setdefault("history", []).append({
                    "name": removed["name"],
                    "emoji": removed["emoji"],
                    "category": removed["category"],
                    "last_seen": datetime.utcnow().isoformat(),
                })
            _save_to_disk()
            return True
    return False


def get_suggestions():
    """Return items seen before but not currently in the fridge."""
    current_names = {i["name"] for i in _cache["items"]}
    return [
        {"name": h["name"], "emoji": h["emoji"], "category": h["category"]}
        for h in _cache.get("history", [])
        if h["name"] not in current_names
    ]


def is_section_stale(section, max_age_seconds=3600):
    """Check if a section's cache is older than max_age_seconds."""
    last = _cache["sections"].get(section, {}).get("last_updated")
    if not last:
        return True
    try:
        dt = datetime.fromisoformat(last)
        age = (datetime.utcnow() - dt).total_seconds()
        return age > max_age_seconds
    except (ValueError, TypeError):
        return True
