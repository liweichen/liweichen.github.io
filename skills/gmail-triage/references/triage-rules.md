# Gmail triage rules

Use this file only when the basic workflow in `SKILL.md` is not enough.

## High-priority cues

Promote a message to `high_priority` when metadata suggests urgency, risk, or a direct ask.

### Sender cues

- Recognized human contacts
- Your manager, client, recruiter, or family member
- Domains tied to finance, legal, healthcare, security, or school administration

### Subject and snippet cues

Common phrases:

- urgent
- asap
- action required
- approval needed
- payment due
- invoice
- verify
- security alert
- interview
- schedule
- meeting request
- contract
- deadline
- today
- tomorrow

### Label cues

Promote when labels include one or more of:

- `IMPORTANT`
- `STARRED`
- `CATEGORY_PERSONAL`
- `UNREAD`

`UNREAD` alone is not enough, but it strengthens other cues.

## Low-priority cues

Use `low_priority` for mail worth keeping but not worth interrupting the user.

Examples:

- Team updates without a direct ask
- Product release notes
- Shipping confirmations
- Calendar reminders for already-accepted events
- Receipts and statements that are informational only

## No-need-to-view cues

Use `no_need_to_view` for messages that are usually safe to batch-ignore.

Examples:

- Promotions and coupons
- Social-network notifications
- Routine marketing campaigns
- Cold sales outreach
- Automated success confirmations for already-completed actions

## Tie-break rules

1. If a message mentions money, security, access, or a meeting request, never put it below `low_priority`.
2. If a message looks like bulk marketing but comes from a real human contact, keep it at least `low_priority`.
3. If the sender is unknown and the content is thin, prefer `no_need_to_view` unless urgency terms are present.
4. If only the snippet indicates urgency, keep `high_priority` but mark the reason as tentative.
