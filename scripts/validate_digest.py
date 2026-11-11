#!/usr/bin/env python3
"""Validate a digest JSON file against the schema the page renders.

Usage: python3 scripts/validate_digest.py [path ...]
Defaults to data/latest.json and data/archive-index.json.
Exits non-zero and lists every problem if the file does not match.
"""
import json
import re
import sys

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECTIONS = ["climate", "weather", "renewables", "science", "industry"]
CARD_FIELDS = ["source", "date", "headline", "url", "summary"]
EVENT_FIELDS = ["name", "status", "impact"]
INDUSTRY_FIELDS = ["date", "title", "body_html", "source_html"]


def check_fields(obj, fields, where, errors):
    if not isinstance(obj, dict):
        errors.append(f"{where}: expected an object")
        return
    for f in fields:
        if not isinstance(obj.get(f), str) or not obj[f].strip():
            errors.append(f"{where}: missing or empty string field '{f}'")
    if "date" in fields and isinstance(obj.get("date"), str) and not DATE.match(obj["date"]):
        errors.append(f"{where}: date '{obj['date']}' is not YYYY-MM-DD")


def validate_digest(d):
    errors = []
    if set(d) != {"digest_date", "metar", "sections"}:
        errors.append(f"top-level keys must be exactly digest_date, metar, sections; got {sorted(d)}")
    if not DATE.match(str(d.get("digest_date", ""))):
        errors.append("digest_date must be YYYY-MM-DD")
    s = d.get("sections")
    if not isinstance(s, dict):
        return errors + ["'sections' object is missing"]
    if set(s) != set(SECTIONS):
        errors.append(f"sections must be exactly {SECTIONS}; got {sorted(s)}")
    for key in SECTIONS:
        sec = s.get(key)
        if not isinstance(sec, dict):
            continue
        if not isinstance(sec.get("items"), list):
            errors.append(f"sections.{key}.items must be an array")
            continue
        if key == "industry":
            for i, it in enumerate(sec["items"]):
                check_fields(it, INDUSTRY_FIELDS, f"sections.industry.items[{i}]", errors)
            continue
        if not isinstance(sec.get("overview_html"), str):
            errors.append(f"sections.{key}.overview_html must be a string")
        for i, it in enumerate(sec["items"]):
            check_fields(it, CARD_FIELDS, f"sections.{key}.items[{i}]", errors)
        if key == "weather":
            if not isinstance(sec.get("major_events"), list):
                errors.append("sections.weather.major_events must be an array (use [] if none)")
            else:
                for i, ev in enumerate(sec["major_events"]):
                    check_fields(ev, EVENT_FIELDS, f"sections.weather.major_events[{i}]", errors)
    return errors


def main(paths):
    failed = False
    for path in paths:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"FAIL {path}: invalid JSON: {e}")
            failed = True
            continue
        if path.endswith("archive-index.json"):
            ok = isinstance(data, list) and all(isinstance(x, str) and DATE.match(x) for x in data)
            errors = [] if ok else ["must be a JSON array of YYYY-MM-DD strings"]
        else:
            errors = validate_digest(data)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK   {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["data/latest.json", "data/archive-index.json"]))
