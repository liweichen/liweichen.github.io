---
name: gmail-triage
description: Review a Gmail inbox and sort messages into high priority, low priority, and no need to view. Use when Codex is asked to check Gmail, triage unread mail, summarize inbox urgency, identify messages that need human attention, or process exported Gmail metadata before drafting a concise inbox report.
---

# Gmail Triage

## Overview

Use this skill to turn raw Gmail message data into a fast triage report. Prefer classifying from message metadata first, then open full bodies only for messages that remain ambiguous or appear high priority.

## Workflow

1. Collect a mailbox snapshot.
2. Normalize each message into a compact record.
3. Classify messages into `high_priority`, `low_priority`, or `no_need_to_view`.
4. Summarize the inbox with clear reasons and suggested follow-up.

## Collect the mailbox snapshot

Choose the lightest-weight source that is already available:

- Use a Gmail API export if OAuth access or a prior tool already exposes message metadata.
- Use a user-provided JSON, CSV, mbox export, or pasted message list if direct Gmail access is unavailable.
- Fetch only recent unread or inbox messages first unless the user explicitly wants a broader sweep.

For each message, keep these fields when available:

- `id`
- `threadId`
- `from`
- `to`
- `subject`
- `snippet`
- `labelIds`
- `internalDate` or another timestamp
- `isUnread`
- `hasAttachments`
- `importance` or Gmail importance markers

Avoid loading full HTML or large bodies until classification requires it.

## Normalize the message list

Convert inputs into a JSON array of compact objects. The bundled script accepts either:

- a top-level JSON array of message objects, or
- an object containing `messages`, `items`, or `threads`

Preferred normalized shape:

```json
[
  {
    "id": "msg-123",
    "from": "Recruiter <jobs@example.com>",
    "subject": "Interview availability for next week",
    "snippet": "Can you share times that work for you?",
    "labelIds": ["INBOX", "UNREAD", "IMPORTANT"],
    "isUnread": true,
    "hasAttachments": false,
    "internalDate": "2026-03-22T09:00:00Z"
  }
]
```

If the source is Gmail API data, map headers into top-level fields before classification. Keep the original raw export separately if later review is needed.

## Classify messages

Run `scripts/classify_messages.py` when you have a JSON export to process. The script uses deterministic heuristics and prints grouped results plus counts.

### High priority

Treat a message as high priority when one or more of these are true:

- It appears to require a response, approval, or time-sensitive action.
- It comes from a human sender and mentions scheduling, deadlines, billing, security, hiring, contracts, legal, production incidents, or account access.
- It carries Gmail urgency markers such as `IMPORTANT`, `CATEGORY_PERSONAL`, or `CATEGORY_UPDATES` plus explicit action language.
- It is unread and recent, especially when the subject or snippet contains words like `urgent`, `ASAP`, `today`, `tomorrow`, `approval`, `invoice`, `payment`, `verify`, `interview`, or `meeting`.

### Low priority

Treat a message as low priority when it may be useful later but does not appear time-sensitive:

- Newsletters, digests, release notes, routine notifications, receipts, or FYI updates.
- Non-urgent work updates with no explicit ask.
- Thread replies that are informative but do not require action right now.

### No need to view

Treat a message as no need to view when it is safe to ignore for the current triage pass:

- Promotions, cold outreach, obvious automated marketing, social notifications, or bulk alerts.
- Duplicate notifications already superseded by another message in the same thread.
- System mail that confirms a completed action and requires no follow-up.

If a message is ambiguous, bias upward into `low_priority` rather than `no_need_to_view`.

Read `references/triage-rules.md` when you need the keyword lists or the tie-break rules.

## Produce the final inbox report

Report results in three sections:

1. `High priority` with one-line reasons and any immediate recommended action.
2. `Low priority` with short summaries.
3. `No need to view` with aggregate patterns instead of listing every item when the volume is high.

Include counts for each category. Mention uncertainty if classification relied only on subject/snippet metadata.

## Use the bundled script

Example:

```bash
python skills/gmail-triage/scripts/classify_messages.py /path/to/messages.json
```

Useful options:

- `--json` to emit machine-readable results.
- `--limit N` to classify only the first `N` messages.

If the script output and your manual review disagree, prefer the manual judgment and explain why.
