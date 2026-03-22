#!/usr/bin/env python3
"""Classify Gmail-style message exports into triage buckets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

HIGH_PRIORITY_TERMS = {
    "urgent",
    "asap",
    "action required",
    "approval",
    "approve",
    "payment",
    "invoice",
    "bill",
    "deadline",
    "today",
    "tomorrow",
    "verify",
    "security",
    "meeting",
    "schedule",
    "interview",
    "contract",
    "access",
    "password",
    "reset",
}

LOW_PRIORITY_TERMS = {
    "newsletter",
    "digest",
    "release notes",
    "receipt",
    "statement",
    "fyi",
    "update",
    "shipping",
    "confirmation",
}

IGNORE_TERMS = {
    "unsubscribe",
    "sale",
    "discount",
    "promo",
    "promotion",
    "webinar",
    "sponsored",
    "cold outreach",
    "follow up",
    "social",
    "suggested for you",
}

HIGH_PRIORITY_LABELS = {"IMPORTANT", "STARRED", "CATEGORY_PERSONAL"}
IGNORE_LABELS = {"CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to a JSON file with message data")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--limit", type=int, default=None, help="Only classify the first N items")
    return parser.parse_args()


def load_messages(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        for key in ("messages", "items", "threads"):
            if isinstance(payload.get(key), list):
                items = payload[key]
                break
        else:
            raise ValueError("Expected a JSON array or an object with messages/items/threads")
    else:
        raise ValueError("Unsupported JSON structure")

    return [normalize_message(item) for item in items]


def normalize_message(item: dict[str, Any]) -> dict[str, Any]:
    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in item.get("payload", {}).get("headers", [])
        if isinstance(header, dict)
    }
    label_ids = item.get("labelIds") or item.get("labels") or []
    record = {
        "id": item.get("id") or item.get("messageId") or "",
        "threadId": item.get("threadId") or "",
        "from": item.get("from") or headers.get("from", ""),
        "to": item.get("to") or headers.get("to", ""),
        "subject": item.get("subject") or headers.get("subject", ""),
        "snippet": item.get("snippet") or "",
        "labelIds": label_ids,
        "isUnread": bool(item.get("isUnread") or "UNREAD" in label_ids),
        "hasAttachments": bool(item.get("hasAttachments") or payload_has_attachments(item)),
        "internalDate": item.get("internalDate") or "",
    }
    return record


def payload_has_attachments(item: dict[str, Any]) -> bool:
    parts = item.get("payload", {}).get("parts", [])
    return any(part.get("filename") for part in parts if isinstance(part, dict))


def score_message(message: dict[str, Any]) -> tuple[str, list[str]]:
    text = " ".join(
        str(message.get(field, "")) for field in ("from", "subject", "snippet")
    ).lower()
    labels = {str(label) for label in message.get("labelIds", [])}
    reasons: list[str] = []
    score = 0

    for term in HIGH_PRIORITY_TERMS:
        if term in text:
            score += 3
            reasons.append(f"matched urgent term: {term}")
    for label in HIGH_PRIORITY_LABELS:
        if label in labels:
            score += 2
            reasons.append(f"important label: {label}")
    if message.get("isUnread"):
        score += 1
        reasons.append("message is unread")
    if message.get("hasAttachments") and any(term in text for term in {"invoice", "contract", "resume"}):
        score += 2
        reasons.append("attachment with likely action-oriented content")

    low_priority_hits = 0
    for term in LOW_PRIORITY_TERMS:
        if term in text:
            low_priority_hits += 1
            reasons.append(f"matched low-priority term: {term}")
    for term in IGNORE_TERMS:
        if term in text:
            score -= 3
            reasons.append(f"matched ignore term: {term}")
    for label in IGNORE_LABELS:
        if label in labels:
            score -= 2
            reasons.append(f"bulk label: {label}")

    if any(term in text for term in {"payment", "invoice", "security", "verify", "meeting", "schedule"}):
        score = max(score, 3)

    if score < 0 and low_priority_hits and not any(term in text for term in IGNORE_TERMS) and not labels.intersection(IGNORE_LABELS):
        score = 0

    if score >= 4:
        return "high_priority", reasons
    if score >= 0:
        return "low_priority", reasons
    return "no_need_to_view", reasons


def classify(messages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {"high_priority": [], "low_priority": [], "no_need_to_view": []}
    for message in messages:
        category, reasons = score_message(message)
        enriched = dict(message)
        enriched["category"] = category
        enriched["reasons"] = reasons
        buckets[category].append(enriched)
    return buckets


def main() -> None:
    args = parse_args()
    messages = load_messages(args.input)
    if args.limit is not None:
        messages = messages[: args.limit]
    buckets = classify(messages)

    if args.json:
        print(json.dumps(buckets, indent=2))
        return

    counts = Counter({name: len(items) for name, items in buckets.items()})
    print("Counts:")
    for name in ("high_priority", "low_priority", "no_need_to_view"):
        print(f"- {name}: {counts[name]}")

    for name in ("high_priority", "low_priority", "no_need_to_view"):
        print(f"\n{name}:")
        if not buckets[name]:
            print("  (none)")
            continue
        for item in buckets[name]:
            subject = item.get("subject") or "(no subject)"
            sender = item.get("from") or "(unknown sender)"
            reasons = "; ".join(item.get("reasons", [])[:3]) or "no strong signal"
            print(f"- {subject} | {sender} | {reasons}")


if __name__ == "__main__":
    main()
