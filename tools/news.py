#!/usr/bin/env python3
"""Validate editions and deterministically rebuild navigation/search/seen state.
Python 3.10+, standard library only. No network, no credentials, no Git writes.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,159}$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
class Invalid(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise Invalid(message)

def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"{path}: expected object")
    return data

def timestamp(value: str) -> datetime:
    require(isinstance(value, str), "timestamp must be a string")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "timestamp must include a UTC offset")
    return result

def day(value: str) -> date:
    require(isinstance(value, str) and bool(DAY.fullmatch(value)), "invalid date format")
    return date.fromisoformat(value)

def url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    try:
        u = urlsplit(value)
        return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password and not any(c.isspace() for c in value)
    except ValueError:
        return False

def text(value: object, maximum: int) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= maximum

def validate_edition(d: dict, categories: set[str]) -> None:
    require(d.get("version") == 1, "unsupported edition version")
    date_value = day(d.get("date"))
    generated = timestamp(d.get("generated_at"))
    require(generated.date() == date_value, "generation date must match edition date")
    require(d.get("kind") in ("daily", "bootstrap"), "kind must be daily or bootstrap")
    require(text(d.get("title"), 160) and text(d.get("summary"), 700), "missing/oversized edition title or summary")
    require(isinstance(d.get("items"), list) and len(d["items"]) <= 12, "edition must contain 0-12 items")
    require(all(isinstance(i, dict) for i in d["items"]), "each item must be an object")
    require(sum(i.get("featured") is True for i in d["items"]) <= 3, "at most 3 featured items")
    events: set[str] = set()
    for i in d["items"]:
        require(isinstance(i, dict), "item must be an object")
        for field in ("id", "event_id"):
            require(isinstance(i.get(field), str) and bool(ID.fullmatch(i[field])), f"invalid {field}")
        require(i["id"].startswith(d["date"] + "-"), "item id must start with edition date")
        require(i["event_id"] not in events, "duplicate event in same edition")
        events.add(i["event_id"])
        require(i.get("category") in categories, "unknown category")
        require(i.get("status") in ("NEW", "UPDATE"), "invalid status")
        require(isinstance(i.get("featured"), bool), "featured must be boolean")
        for field, limit in (("title", 180), ("summary", 1200), ("why_you_care", 600)):
            require(text(i.get(field), limit), f"missing/oversized {field}")
        require("published_date" in i and "event_date" in i, "explicit publication/event dates (or null) required")
        for field in ("published_date", "event_date"):
            if i[field] is not None:
                actual = day(i[field])
                if field == "published_date":
                    require(actual <= date_value, "publication date is after edition date")
        verified = timestamp(i.get("verified_at"))
        require(verified <= generated, "verification is after edition generation")
        if d["kind"] == "daily":
            require(i["published_date"] is not None, "daily item requires a verified publication date")
            age_days = (date_value-day(i["published_date"])).days
            if i.get("published_at"):
                published = timestamp(i["published_at"])
                require(published.date() == day(i["published_date"]), "publication timestamp/date mismatch")
                require(0 <= (generated-published).total_seconds() <= 72*3600, "daily item outside 72-hour window")
            else:
                require(age_days <= 2, "date-only source is too old to establish a 72-hour window")
            if age_days > 1:
                require(text(i.get("recency_reason"), 400), "older daily item needs recency_reason")
        require(isinstance(i.get("sources"), list) and len(i["sources"]) > 0, "source required")
        for s in i["sources"]:
            require(isinstance(s, dict) and text(s.get("name"), 150) and url(s.get("url")), "invalid source")
            require(s.get("type") in ("official", "research", "reputable", "community"), "invalid source type")
        require(isinstance(i.get("tags"), list) and all(text(t, 80) for t in i["tags"]), "invalid tags")
        image = i.get("image")
        if image is not None:
            require(isinstance(image, dict) and url(image.get("url")) and url(image.get("source_url")), "invalid image URL/provenance")
            require(text(image.get("alt"), 250) and text(image.get("credit"), 150), "image alt/credit required")
        if i["status"] == "UPDATE":
            require(text(i.get("delta"), 800), "UPDATE needs a material delta")
            previous = i.get("previous", {})
            require(bool(ID.fullmatch(previous.get("id", ""))) and day(previous.get("date")) < date_value, "UPDATE needs a prior article")

def editions(root: Path) -> list[dict]:
    config = load(root / "docs/data/categories.json")
    cats = {c["id"] for c in config["categories"]}
    require(len(cats) == len(config["categories"]) and len(cats)>0, "duplicate/empty categories")
    result, ids, events = [], set(), {}
    for path in sorted((root / "docs/data/daily").glob("*.json")):
        d = load(path)
        validate_edition(d, cats)
        require(path.stem == d["date"], "filename does not match date")
        for i in d["items"]:
            require(i["id"] not in ids, "duplicate article id")
            ids.add(i["id"])
            prior = events.get(i["event_id"])
            if i["status"] == "UPDATE":
                require(prior is not None, "UPDATE event has no prior record")
                require(i["previous"] == {"id":prior["id"], "date":prior["date"]}, "UPDATE must link the latest previous record for this event")
                require(i["summary"] != prior["summary"], "UPDATE repeats the previous summary")
            else:
                require(prior is None, "known event cannot be labelled NEW")
            events[i["event_id"]] = {**i, "date": d["date"]}
        result.append(d)
    return result

def derived(root: Path, days: list[dict]) -> dict[str, dict]:
    settings = load(root / "config/pipeline.json")
    ordered = list(reversed(days))
    newest = ordered[0]["date"] if ordered else None
    generated = max((d["generated_at"] for d in days), key=timestamp) if days else None
    manifest = {"version":1, "latest":newest, "updated_at":generated, "editions":[{"date":d["date"], "title":d["title"], "kind":d["kind"], "count":len(d["items"]), "categories":sorted({i["category"] for i in d["items"]}), "path":f"data/daily/{d['date']}.json"} for d in ordered]}
    search = {"version":1,"items":[]}
    for d in ordered:
        for i in d["items"]:
            search["items"].append({"id":i["id"],"event_id":i["event_id"],"edition":d["date"],"category":i["category"],"title":i["title"],"search_text":" ".join([i["title"],i["summary"],i["why_you_care"],*i["tags"],*(s["name"] for s in i["sources"])])})
    event_map = {}
    for d in days:
        for i in d["items"]:
            first = event_map.get(i["event_id"], {}).get("first_seen", d["date"])
            event_map[i["event_id"]] = {"event_id":i["event_id"],"first_seen":first,"last_seen":d["date"],"last_item_id":i["id"],"title":i["title"],"last_summary":i["summary"],"sources":[s["url"] for s in i["sources"]]}
    cutoff = day(newest) - timedelta(days=settings["state_retention_days"]-1) if newest else date.min
    seen = [e for e in event_map.values() if day(e["last_seen"]) >= cutoff]
    seen.sort(key=lambda e:(e["last_seen"],e["event_id"]),reverse=True)
    return {"docs/data/index.json":manifest,"docs/data/search.json":search,"state/seen.json":{"version":1,"as_of":newest,"retention_days":settings["state_retention_days"],"max_events":settings["state_max_events"],"events":seen[:settings["state_max_events"]]}}

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temporary.replace(path)

def run(root: Path, command: str) -> int:
    days = editions(root)
    outputs = derived(root, days)
    for path, data in outputs.items():
        if command == "rebuild":
            write_json(root/path,data)
        else:
            require((root/path).exists() and load(root/path)==data,f"{path} is out of sync: run rebuild")
    print(f"OK: {len(days)} editions, {sum(len(d['items']) for d in days)} articles; data/index/search/seen consistent.")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["validate","rebuild"])
    parser.add_argument("--root",type=Path,default=ROOT)
    args=parser.parse_args()
    try:
        return run(args.root,args.command)
    except (Invalid, ValueError, TypeError, KeyError, OSError) as e:
        print(f"ERROR: {e}",file=sys.stderr)
        return 1
if __name__ == "__main__":
    raise SystemExit(main())
