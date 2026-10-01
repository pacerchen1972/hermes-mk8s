---
name: create-pcpm-ticket
description: Use when a piece of PM work exists (SACOM ticket, vault task, engineering ticket) but no PCPM ticket has been created yet, or when explicitly asked to open a PCPM ticket.
---

# Create PCPM Ticket

Create a PCPM Task (or Improvement/Feature) ticket from scratch and link it to related tickets.

## When to Use

- A SACOM, CSMCIC, TWT, or engineering ticket exists but no PCPM ticket was ever created
- A vault task note has an empty `pcpm_ticket:` field
- User says "create/open a PCPM ticket for this"

## Step 1 — Gather info

Collect (from conversation context or ask the user):

| Field | Default | Notes |
|---|---|---|
| Summary | — | `[Product] Short description` format, e.g. `[PostgreSQL] Deprecated PostgreSQL v14` |
| Type | Task | Task / Improvement / Feature |
| Description | — | See template below |
| Related tickets | — | SACOM-XXXX, TWT-XXXX, CSMCIC-XXXX, etc. |
| Parent epic | — | PCPM-630 (MK8s), PCPM-871 (DBaaS roadmap), PCPM-720 (TWT/AI Studio) |

**Summary format:** `[ProductArea] Action or subject` — match the pattern of existing PCPM tickets.

## Step 2 — Create the ticket

```python
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.jira-config'))
from jira_helper import create_pcpm_ticket, get_session

description = """[Brief explanation of why this ticket exists]

[Bullet list of key facts: dates, versions, affected counts, etc.]

Related tickets:
* [SACOM-XXXX|https://hosting-jira.1and1.org/browse/SACOM-XXXX] -- [description]
* [TWT-XXXX|https://hosting-jira.1and1.org/browse/TWT-XXXX] -- [description]"""

key = create_pcpm_ticket(
    summary="[Product] Short description",
    description=description,
    epic_link="PCPM-XXX",  # omit if no parent epic
)
```

`create_pcpm_ticket` creates the ticket as **Task** type, assigned to **rdelarrearemiro**, and links to `epic_link` as "Relates" if provided.

## Step 3 — Link related tickets (bidirectional)

If there are related tickets not already in the description, link them:

```python
s = get_session()
for related_key in ["SACOM-9089", "TWT-3420"]:
    s.post(f"{s._jira_server}/rest/api/2/issueLink", json={
        "type": {"name": "Relates"},
        "inwardIssue": {"key": key},
        "outwardIssue": {"key": related_key},
    }).raise_for_status()
    print(f"Linked {key} → {related_key}")
```

## Step 4 — Report back

```
✅ PCPM-XXX created: [Product] Short description
   URL: https://hosting-jira.1and1.org/browse/PCPM-XXX
   Linked to: SACOM-XXXX, TWT-XXXX (if applicable)

📌 Next: add pcpm_ticket: PCPM-XXX to vault task frontmatter (if task note exists)
```

## Parent Epics Quick Reference

| Area | Parent Epic |
|---|---|
| Managed Kubernetes (MK8s) | PCPM-630 |
| DBaaS roadmap | PCPM-871 |
| TWT / AI Model Studio docs | PCPM-720 |
| EAKS P&L | PCPM-631 (child) |

## Common Mistakes

- **Wrong type:** Use Task for concrete work, Improvement for enhancements, Feature for new capabilities. Default = Task.
- **Skipping the parent epic link:** Always check if there's a parent epic (see table above) — link it via `epic_link` or manually after.
- **No backlink in related tickets:** The description should include JIRA wiki markup links to all related tickets so they show in the ticket view.
- **Improvement vs Task:** If it's a customer-facing change or enhancement to an existing feature, use Improvement. Pure PM coordination → Task.
