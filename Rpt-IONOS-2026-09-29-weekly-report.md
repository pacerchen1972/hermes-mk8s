---
name: Weekly Report — Week of 2026-09-29
type: report
created: 2026-10-01
updated: 2026-10-01
area: IONOS
tags: [weekly-report]
---

## Weekly Work Report — Week of 2026-09-29

> Week: 29 September – 1 October 2026 (partial — Thursday cut-off)

---

### Summary by Initiative

---

**[DBaaS MongoDB] v2 Launch — PCPM-859 / PCPM-860**

- [[PCPM-860]] Internal Sales & Support Briefing for MongoDB v2 **resolved** — briefing sent to `sales.organisation@ionos.com` and Customer Care Cloud before customer communication date (15 September 2026)
- [[PCPM-859]] Documentation update for docs.ionos.com **in progress** as of launch day (1 October 2026): backup retention (7 days → 1–365 days configurable), Playground edition removed from Overview/Editions and Resource Allocation pages

**Outcome:** MongoDB v2 launched on 1 October 2026 with internal teams briefed and docs in progress.

---

**[Event Streams for Apache Kafka] Kafka 4.0 SACOM — PCPM-940**

- New PCPM ticket [[PCPM-940]] created: customer communication (SACOM A2, DE) for automatic version migration from 3.9.x to 4.0.0, planned migration date 15 November 2026
- No downtime, no customer action required — IONOS executes the migration fully
- Pending: engineering confirmation of client compatibility (3.9.x → 4.0.0) and documentation link for IONOS Cloud Docs

**Outcome:** Communication scope defined and ticket created; engineering sign-off outstanding.

---

**[DBaaS] ITIL Incident Management Dashboard — PCPM-760**

- Continued work on DBaaS incident KPI dashboard (PostgreSQL, MongoDB, MariaDB, In-Memory DB)
- Ticket remains open; iterative progress tracked under [[PCPM-760]]

---

**[Claude Code / Tooling] `create-pcpm-ticket` Skill**

- Built and committed new Claude Code skill `/create-pcpm-ticket` (commit `102b201`, branch `worktree-create-pcpm-ticket-skill`)
- Skill automates creation of PCPM tickets from SACOM, TWT, vault task, or engineering ticket context
- Covers: summary format (`[ProductArea] description`), JIRA-wiki description template, parent epic linking (PCPM-630 MK8s / PCPM-871 DBaaS / PCPM-720 AI Studio), and bidirectional link instructions

**Outcome:** Repeatable workflow for PCPM ticket creation now codified as a reusable Claude Code skill.

---

### JIRA Tickets Touched

| Ticket | Summary | Status |
|--------|---------|--------|
| [PCPM-940](https://jira.ionos.org/browse/PCPM-940) | Event Streams: Kafka 3.9→4.0 SACOM customer communication | Open |
| [PCPM-859](https://jira.ionos.org/browse/PCPM-859) | [DBaaS MongoDB] v2 Launch — Documentation Update (TWT) | In Progress |
| [PCPM-860](https://jira.ionos.org/browse/PCPM-860) | [DBaaS MongoDB] v2 Launch — Internal Sales & Support Briefing | Resolved |
| [PCPM-760](https://jira.ionos.org/browse/PCPM-760) | ITIL Incident Management Dashboard — DBaaS | Open |
| [PCPM-631](https://jira.ionos.org/browse/PCPM-631) | [Event Streams] Product Improvements | Open |

---

### Files & Outputs Created

- `~/.claude/skills/create-pcpm-ticket/` — new Claude Code skill, commit `102b201`
- `Rpt-IONOS-2026-09-29-weekly-report.md` — this report

---

### Next Steps

- [ ] Engineering sign-off on Kafka 3.9→4.0 client compatibility (PCPM-940)
- [ ] Add docs link to PCPM-940 once Kafka 4.0 docs are live
- [ ] Complete and merge MongoDB v2 docs (PCPM-859) — pages: Backup & Recovery, Overview/Editions, Resource Allocation
- [ ] Progress ITIL Incident Management Dashboard for DBaaS (PCPM-760)
- [ ] Merge `worktree-create-pcpm-ticket-skill` branch → main (create-pcpm-ticket skill)
