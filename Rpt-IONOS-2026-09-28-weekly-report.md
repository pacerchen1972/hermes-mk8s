---
name: Weekly Report — Week of 2026-09-28
type: report
created: 2026-10-05
updated: 2026-10-05
area: IONOS
tags: [weekly-report]
---

## Weekly Work Report — Week of 2026-09-28

> Week: 28 September – 2 October 2026

---

### Summary by Initiative

---

**[DBaaS MongoDB] v2 Launch & Migration — PCPM-857**

- [[PCPM-860]] Internal Sales & Support Briefing **resolved** — sent to `sales.organisation@ionos.com` and Customer Care Cloud
- [[PCPM-858]] Customer communication drafted and in progress — target send date 1 October 2026; informs all existing MongoDB customers of v2 launch and migration schedule for October
- [[PCPM-859]] TWT documentation update in progress — backup retention (7 days → 1–365 days configurable), Playground edition removed, storage class updated to Performance-only
- MongoDB v2 **launched 1 October 2026** — clusters migrating throughout October

**Outcome:** MongoDB v2 GA on 1 October. Customers notified, sales briefed, docs in progress.

---

**[DBaaS MongoDB] v2 Product Website Update — PCPM-941**

- New ticket [[PCPM-941]] created: `cloud.ionos.de/managed/dbaas/managed-mongodb` page update before v2 GA date of **13 November 2026**
- [[PCPM-943]] Task to request marketing open MKTCLOUD ticket — open
- [[PCPM-944]] Task to attach PM briefing (Playground removal, MongoDB 8.0, configurable backup 1–365 days, Observability integration, new API endpoint `mongodb.<region>.ionos.com`, v1 EOL 13.11.2026) — open
- [[PCPM-945]] Task to review and approve final marketing copy before 13.11.2026 — open

**Outcome:** Full website update pipeline scoped and ticketed for MongoDB v2 GA in November.

---

**[PostgreSQL] v14 Deprecation — PCPM-946**

- [[PCPM-946]] **Resolved** — PostgreSQL v14 deprecation communication sent to customers on 1 October 2026
- Deprecation date: 31 December 2026; target version: PostgreSQL v16

**Outcome:** Customer notification delivered on schedule.

---

**[EAKS] Pricing Review — PCPM-947**

- New ticket [[PCPM-947]] created: pricing review for EAKS (Event Streams for Apache Kafka) to increase list prices and close feature gaps to restore margin
- DBR1 COGS analysis (2026-10-01) with verified operator sizes (`kaas-operator-size-config.yaml`) shows S and M flavors are loss-making at current realized prices (~34% of list)
- Competitive benchmark (8 providers): Schema Registry, Kafka Connect, REST Proxy missing — primary deal blocker across all main competitors
- Status: Preparing

**Outcome:** EAKS pricing and feature gap analysis initiated; S/M margin problem quantified.

---

**[Event Streams] Kafka 4.0 SACOM — PCPM-940**

- [[PCPM-940]] Customer communication (SACOM A2, DE) scoped for Kafka 3.9.x → 4.0.0 automatic migration, planned 15 November 2026
- Pending: engineering sign-off on client compatibility + docs link

**Outcome:** Communication spec ready; blocked on engineering confirmation.

---

**[DBaaS] Roadmap Q4 2026–Q4 2027 — PCPM-871**

- [[PCPM-871]] Roadmap ticket active — iterative progress on the 26-feature-request portfolio

---

**[Claude Code / Tooling] `create-pcpm-ticket` Skill**

- New skill `/create-pcpm-ticket` built and committed (`102b201`, 2026-10-01)
- Automates PCPM ticket creation from SACOM, TWT, vault task, or engineering ticket context
- Also built: improved `/weekly-report` skill (correct this-week/last-week date scripts, Bash-blocked warning, git log step, worktree fallback) and `P-20261002-claude-code-skills-reference.md` — portable skills reference for any machine

**Outcome:** Three tooling deliverables shipped; PCPM workflow now has a dedicated skill.

---

### JIRA Tickets Touched

| Ticket | Summary | Status |
|--------|---------|--------|
| [PCPM-947](https://jira.ionos.org/browse/PCPM-947) | EAKS Pricing Review — restore margin, close feature gaps | Preparing |
| [PCPM-946](https://jira.ionos.org/browse/PCPM-946) | [PostgreSQL] Deprecated PostgreSQL v14 | **Resolved** |
| [PCPM-945](https://jira.ionos.org/browse/PCPM-945) | Review and approve MongoDB v2 marketing copy | Open |
| [PCPM-944](https://jira.ionos.org/browse/PCPM-944) | Attach PM briefing to MKTCLOUD ticket | Open |
| [PCPM-943](https://jira.ionos.org/browse/PCPM-943) | Request marketing to open MKTCLOUD ticket | Open |
| [PCPM-941](https://jira.ionos.org/browse/PCPM-941) | MongoDB v2 — product website update (cloud.ionos.de) | Open |
| [PCPM-940](https://jira.ionos.org/browse/PCPM-940) | Event Streams: Kafka 3.9→4.0 SACOM communication | Open |
| [PCPM-860](https://jira.ionos.org/browse/PCPM-860) | [DBaaS MongoDB] v2 — Internal Sales & Support Briefing | **Resolved** |
| [PCPM-859](https://jira.ionos.org/browse/PCPM-859) | [DBaaS MongoDB] v2 — Documentation Update (TWT) | In Progress |
| [PCPM-858](https://jira.ionos.org/browse/PCPM-858) | [DBaaS MongoDB] v2 — Customer Communication | In Progress |
| [PCPM-857](https://jira.ionos.org/browse/PCPM-857) | [DBaaS MongoDB] v2 Launch & Migration — October 2026 | In Progress |
| [PCPM-871](https://jira.ionos.org/browse/PCPM-871) | [DBaaS] Product Roadmap Q4 2026–Q4 2027 | In Progress |
| [PCPM-760](https://jira.ionos.org/browse/PCPM-760) | ITIL Incident Management Dashboard — DBaaS | Open |
| [PCPM-631](https://jira.ionos.org/browse/PCPM-631) | [Event Streams] Product Improvements | Open |
| [PCPM-627](https://jira.ionos.org/browse/PCPM-627) | [DBaaS MongoDB] Product Improvements | In Progress |

---

### Files & Outputs Created

- `~/.claude/skills/create-pcpm-ticket/` — new Claude Code skill, commit `102b201`
- `~/.claude/skills/weekly-report/SKILL.md` — improved weekly-report skill
- `P-20261002-claude-code-skills-reference.md` — portable skills reference doc
- `Rpt-IONOS-2026-09-29-weekly-report.md` — mid-week report (Thu cut-off)
- `Rpt-IONOS-2026-09-28-weekly-report.md` — this report

---

### Next Steps

- [ ] Send MongoDB v2 customer communication (PCPM-858) — was targeting 1 October
- [ ] Contact marketing to open MKTCLOUD ticket (PCPM-943)
- [ ] Attach PM briefing to MKTCLOUD (PCPM-944)
- [ ] Engineering sign-off: Kafka 3.9→4.0 client compatibility (PCPM-940)
- [ ] Complete MongoDB v2 TWT docs: Backup & Recovery, Overview/Editions, Resource Allocation (PCPM-859)
- [ ] EAKS pricing proposal — next steps after COGS analysis (PCPM-947)
- [ ] Merge `worktree-create-pcpm-ticket-skill` → main
