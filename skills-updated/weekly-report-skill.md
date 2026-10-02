---
name: weekly-report
description: Use when generating a structured weekly work report — this week, last week, or a specific week. Pulls JIRA/PCPM tickets updated that week, reads vault notes modified that week, and formats into a manager-shareable summary saved to the Reports folder.
---

# Weekly Report

Generate a structured weekly work report covering JIRA activity, Obsidian vault changes, and Claude Code session outputs.

---

## Step 0 — Clarify which week

Ask the user which week they want **if not already stated**:

- **This week** (current Monday – today)
- **Last week** (previous Monday – Friday)
- **A specific week** (provide start and end dates)

Do NOT assume — "this week" and "last week" produce different results.

---

## Step 1 — Compute the date range

Run the correct snippet based on the user's answer:

**This week (Monday to today):**
```bash
python3 - <<'EOF'
from datetime import date, timedelta
today = date.today()
monday = today - timedelta(days=today.weekday())
print(f"WEEK_START={monday.isoformat()}")
print(f"WEEK_END={today.isoformat()}")
print(f"TODAY={today.isoformat()}")
EOF
```

**Last week (Monday to Friday):**
```bash
python3 - <<'EOF'
from datetime import date, timedelta
today = date.today()
last_monday = today - timedelta(days=today.weekday() + 7)
last_friday = last_monday + timedelta(days=4)
print(f"WEEK_START={last_monday.isoformat()}")
print(f"WEEK_END={last_friday.isoformat()}")
print(f"TODAY={today.isoformat()}")
EOF
```

Use `WEEK_START`, `WEEK_END`, and `TODAY` in all subsequent steps.

---

## Step 2 — JIRA/PCPM activity

```bash
python3 ~/.jira-config/jira_helper.py search "project = PCPM AND assignee = rdelarrearemiro AND updated >= '{WEEK_START}' AND updated <= '{WEEK_END}' ORDER BY updated DESC" 2>&1
```

For each ticket returned, fetch details:
```bash
python3 ~/.jira-config/jira_helper.py get {TICKET-KEY} 2>&1 | head -15
```

---

## Step 3 — Obsidian vault notes modified this week

**CRITICAL:** Use `Grep` tool (not Bash) for `~/Documents/` — macOS blocks Bash/find/ls there.

Search pattern: `updated: (WEEK_START|day2|day3|day4|WEEK_END)`

Search in these paths:
- `~/Documents/IONOS-Obsidian/101 - Tasks/`
- `~/Documents/IONOS-Obsidian/200 - Projects/`
- `~/Documents/IONOS-Obsidian/300 - Reports/`
- `~/Documents/IONOS-Obsidian/000 - Inbox/`

For each file found, read the first 20 lines to extract: title, pcpm_ticket, status, type.

---

## Step 4 — Claude Code session output (this week)

Check git log for code work done this week:

```bash
git log --format="%h %ad %s" --date=short --since="{WEEK_START}" --until="{WEEK_END}" --all 2>/dev/null | head -20
```

Also check known repos if accessible (use `-C` only if not in a worktree session):
- `~/Git/dev-agents`
- `~/Git/ionos-provisioning-benchmark`
- `~/Coding/product-dashboard`

Note any skills created, tools built, or automation written.

---

## Step 5 — Format and save the report

**Output structure:**

```markdown
## Weekly Work Report — Week of {WEEK_START}

> Week: {WEEK_START} – {WEEK_END}

### Summary by Initiative

**[Initiative / PCPM-XXX]**
- Action taken
- Decision made
- Output created

**Outcome:** One-line result.

### JIRA Tickets Touched

| Ticket | Summary | Status |
|--------|---------|--------|
| PCPM-XXX | ... | Open |

### Files & Outputs Created or Updated
- `T-IONOS-XXX` — description
- `PRJ-IONOS-XXX` — description
- `Rpt-IONOS-YYYYMMDD-...` — description
- `skill-name` or `commit-hash` — description

### Next Steps
- [ ] Item (PCPM-XXX)
```

**Rules:**
- Group JIRA tickets under their parent initiative
- One line per action — no filler
- Always include an **Outcome:** line per initiative
- Report must be shareable with a manager as-is

---

## Step 6 — Save the report

**Standard save path:**
`~/Documents/IONOS-Obsidian/300 - Reports/Rpt-IONOS-{WEEK_START}-weekly-report.md`

**If in a worktree session** (cwd is under `.claude/worktrees/`), write to the worktree instead and give the user this copy command:
```bash
cp ~/.claude/worktrees/<branch>/Rpt-IONOS-{WEEK_START}-weekly-report.md ~/Documents/IONOS-Obsidian/300\ -\ Reports/
```

**Frontmatter:**
```yaml
---
name: Weekly Report — Week of {WEEK_START}
type: report
created: {TODAY}
updated: {TODAY}
area: IONOS
tags: [weekly-report]
---
```
