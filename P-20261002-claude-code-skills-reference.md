---
name: Claude Code Skills Reference
type: permanent-note
created: 2026-10-02
updated: 2026-10-02
area: IONOS
tags: [claude-code, skills, reference, tooling]
---

# Claude Code Skills Reference

This document is a self-contained reference for all Claude Code skills available in Ricardo's setup. It is designed to be portable — readable on any machine, with or without memory files or the skills directory, so you can reconstruct the full workflow from scratch.

---

## How Skills Work

**Claude Code skills** are markdown files stored in `~/.claude/skills/<skill-name>/skill.md`. They are invoked with a slash command: `/skill-name` or via the `Skill` tool inside an agentic session.

When you type `/weekly-report`, Claude loads the skill file and follows it as a workflow instruction. Skills are:
- Reusable — work across sessions and machines
- Composable — one skill can call another
- Context-portable — you can share a skill file and it runs identically elsewhere

**Key paths:**
- Skills directory: `~/.claude/skills/`
- Memory directory: `~/.claude/projects/-Users-ricardodelarrearemiro/memory/`
- Memory index: `~/.claude/projects/-Users-ricardodelarrearemiro/memory/MEMORY.md`
- Settings: `~/.claude/settings.json`
- JIRA helper: `~/.jira-config/jira_helper.py`

**IONOS-specific constraint:** Bash is blocked for `~/Documents/` on macOS (Full Disk Access not granted to terminal). Always use the `Grep` or `Read` tools from Claude Code instead of shell commands when accessing `~/Documents/IONOS-Obsidian/`.

---

## Vault Structure (IONOS-Obsidian)

```
~/Documents/IONOS-Obsidian/
  000 - Inbox/          # New tasks before JIRA ticket exists
  101 - Tasks/          # Active tasks (T-IONOS-NNN-title.md)
  200 - Projects/       # Project notes (PRJ-IONOS-NNN-title.md)
  300 - Reports/        # Output reports (Rpt-IONOS-YYYYMMDD-title.md)
  900 - Permanent Notes/ # Reference docs (P-YYYYMMDD-title.md)
  104 - Claude/         # Claude-specific assets (PPTX templates, etc.)
  Templates/            # Task, project, report templates
```

**Task lifecycle:** Inbox → (PCPM ticket created) → 101 - Tasks/

**Every task in 101 - Tasks/ MUST have a `pcpm_ticket:` frontmatter field** linking to a PCPM JIRA ticket. This is enforced by the CLAUDE.md global rule.

---

## Daily / Weekly Workflow Skills

### `/today`
**What it does:** Shows today's task overview across all Obsidian vaults (IONOS, BcmA, Pandarve, TanitRic). Auto-promotes inbox tasks with `actionable: yes` to 101 - Tasks/. On Mondays, also generates copy-paste JIRA tables for Weekly Meeting Prep (14h) and DBaaS PO Meeting (16h).

**Variants:** `/today ionos`, `/today personal`, `/today bcma`

---

### `/weekly-report`
**What it does:** Generates a structured weekly work report. Asks which week (this week / last week / specific). Pulls PCPM JIRA tickets updated that week, Obsidian notes with matching `updated:` dates, and git commits. Saves to `300 - Reports/Rpt-IONOS-WEEK_START-weekly-report.md`.

**Key sections:** Summary by initiative, JIRA tickets table, files/outputs created, next steps.

**Note:** If running in a worktree session, writes to the worktree and gives you a `cp` command to move the file to the vault.

---

### `/work-report`
**What it does:** Daily version of the weekly report. Pulls JIRA tickets updated today and Obsidian notes modified today. Formats into a shareable daily summary.

---

### `/work-comms`
**What it does:** Generates a SACOM communications status report — all open customer communications, upcoming sends, and audience conflict checks. Use before scheduling a new SACOM send.

---

### `/vault-cleanup`
**What it does:** Weekly hygiene — reconciles project notes, task notes, and PCPM tickets. Classifies every task as: (A) linked to existing project, (B) needs new project, or (C) orphan. Report-only; never modifies vault files.

---

## Task & Ticket Management

### `/new-task`
**What it does:** Creates a new vault task note with the correct naming convention: `T-AREA-SEQ-title.md`. Prompts for area (IONOS, BcmA, TR), title, and frontmatter fields. Places in `000 - Inbox/` until a PCPM ticket is ready.

---

### `/new-idea`
**What it does:** Creates a new idea note with Zettelkasten naming (`I-YYYYMMDD-title.md`). For capturing product ideas, feature requests, or research hypotheses.

---

### `/create-pcpm-ticket`
**What it does:** Creates a PCPM JIRA ticket from context. Use when a vault task, SACOM ticket, TWT ticket, or engineering ticket exists but no PCPM ticket has been linked yet.

**Workflow:**
1. Collects: summary (format: `[ProductArea] Short description`), type (Task/Improvement/Feature), description, related tickets
2. Identifies parent epic: PCPM-630 (MK8s), PCPM-871 (DBaaS roadmap), PCPM-720 (AI Studio/TWT)
3. Generates paste-ready JIRA-wiki-markup (Ricardo creates the ticket manually — no JIRA write access)
4. Outputs bidirectional link instructions

**Key rule from CLAUDE.md:** Ricardo creates the ticket manually; Claude delivers the markup block. Never attempt JIRA write via API.

---

## JIRA / Confluence Skills (Atlassian Suite)

### `/atlassian:capture-tasks-from-meeting-notes`
**What it does:** Reads meeting notes and extracts actionable tasks, creating vault task entries for each.

### `/atlassian:generate-status-report`
**What it does:** Generates a status report from JIRA tickets for a project or sprint.

### `/atlassian:jira-sprint-dashboard`
**What it does:** Builds a sprint dashboard from JIRA sprint data.

### `/atlassian:search-company-knowledge`
**What it does:** Searches Confluence for company knowledge. Useful for policies, processes, and product facts.

### `/atlassian:spec-to-backlog`
**What it does:** Converts a product spec or PRD into a JIRA backlog with epics, stories, and acceptance criteria.

### `/atlassian:triage-issue`
**What it does:** Triages a JIRA issue — classifies severity, suggests owner, checks for related tickets.

---

## IONOS Product Skills

### `/customer-communication-mail`
**What it does:** Drafts IONOS customer-facing emails for product/platform changes (deprecations, new limits, API changes, lifecycle policies, version migrations). Follows IONOS SACOM tone, structure, and style.

**SACOM process:** A2 = customer impact notification; Change L = customer agreement required (termination right triggered).

**Key rule:** Do NOT add AGB §5.3 termination-right phrase — Ricardo's position is that the applicable T&C are not valid.

---

### `/ionos-inside-sales-briefing`
**What it does:** Drafts the internal Sales & Customer Support enablement mail (sent to `sales.organisation@ionos.com`) ahead of a customer SACOM. The "heads-up before your accounts ask" for product changes, migrations, or deprecations.

**Trigger:** Use before any customer-facing communication goes out.

---

### `/ionos-dbaas-fact-checker`
**What it does:** Fact-checks a full marketing document, blog post, sales deck, or customer-facing page that makes claims about IONOS DBaaS (PostgreSQL, MariaDB, MongoDB, In-Memory DB/Valkey). Catches false, outdated, or unverifiable statements against the DBaaS facts knowledge base.

**Source of truth:** `~/.claude/skills/ionos-dbaas-fact-checker/facts/*.md`

---

### `/ionos-dbaas-change-factcheck`
**What it does:** Fact-checks only the CHANGED portions of a DBaaS document — a redline, diff, or before/after comparison. Faster than the full fact-checker when you only modified a section.

---

### `/ionos-mongodb-consultant`
**What it does:** Activates a MongoDB consultant persona. Asks targeted questions about the customer's use case (data volume, query patterns, HA requirements) before making sizing and architecture recommendations for IONOS DBaaS MongoDB.

---

### `/ionos-mongodb-provision`
**What it does:** Generates provisioning payloads (API JSON or Terraform) for an IONOS DBaaS MongoDB cluster. Covers: edition choice (Business/Enterprise), RAM sizing, WiredTiger cache calculation, connection limits, network configuration.

---

### `/ionos-product-comparison`
**What it does:** Compares an IONOS product (from Ricardo's PM portfolio) or an external product against competitors from a technical PM or commercial PM standpoint. Produces feature gaps, pricing comparison, and roadmap implications.

**Portfolio:** Managed Kubernetes (MK8s), DBaaS (PostgreSQL, MongoDB, MariaDB, In-Memory DB/Valkey), Private Container Registry (PCR), AI Model Studio, Event Streams for Apache Kafka.

---

### `/mk8s-docs-audit`
**What it does:** Audits a product documentation set by tracing customer journeys through the live docs pages. Classifies each journey step as Missing / Incomplete / Unlinked / Fragmented. Outputs a phased, prioritized backlog.

**Default target:** IONOS Managed Kubernetes docs. Reusable for DBaaS, PCR, and other products.

---

### `/mk8s-private-cluster-design`
**What it does:** Designs, sizes, or quotes an IONOS MK8s private cluster setup. Covers: private vs public node pools, private API endpoint options, ingress on private clusters, egress, NAT gateway sizing, on-prem connectivity.

**Key fact:** MK8s cluster resources can only be placed in `de` (Berlin) or `fra` (Frankfurt). Node pools can be placed in any DC. The `public` flag is cluster-level and immutable.

---

### `/product-book`
**What it does:** Creates or updates a Product Book for an IONOS Cloud product. Guides the PM through section-by-section questions, decision gates, and output generation. Covers: product vision, ICP, pricing, competitive positioning, roadmap.

---

## Research & Analysis

### `/cloud-market-research`
**What it does:** Compares cloud services, features, or pricing across providers (GPU instances, managed K8s, DBaaS, container registries, AI/ML, storage). Use for competitive analysis, RFP/tender pricing research, or pricing model design.

---

### `/confidential-kubernetes-research`
**What it does:** Researches competitors offering Confidential Kubernetes, Confidential Computing for containers, or TEE-based K8s services. Produces competitor profiles and a landscape summary.

---

### `/venture-competitor-research`
**What it does:** Discovers and profiles competitors for a venture, startup, or product. Synthesizes strategic insights from features/pricing/positioning analysis.

---

### `/hugging-face-paper-pages`
**What it does:** Reads a Hugging Face paper page or arXiv paper and returns a structured summary. Also queries the papers API for metadata: authors, linked models/datasets/spaces, GitHub repo, project page.

---

## Infrastructure & Benchmarks

### `/hermes-compute-sweep`
**What it does:** Runs the monthly compute provisioning benchmark sweep on `hermes-standalone` (IONOS VM at `100.70.50.72` via Tailscale) and optionally Digital Ocean. Rebuilds the dashboard and syncs results locally.

**Variants:** `/hermes-compute-sweep ionos`, `/hermes-compute-sweep do`, `/hermes-compute-sweep both`, `/hermes-compute-sweep sync`

**Repo:** `~/Git/ionos-provisioning-benchmark`

---

### `/valkey-benchmark-sweep`
**What it does:** Runs monthly Valkey (In-Memory DB) benchmarks across IONOS and Digital Ocean. Tracks performance trends for product stability KPIs.

---

### `/ionos-hermes-setup`
**What it does:** Automates the IONOS Hermes Agent setup: Docker build/push to Private Container Registry, Kubernetes secret creation, and deployment verification on MK8s.

**Live deployment:** Pod `hermes-agent-0`, Llama-3.3-70B via IONOS AI Model Hub, kubeconfig at `~/.kube/hermes-mk8s.yaml`.

---

## Claude Code / Tooling Skills

### `/sync-obsidian-claude`
**What it does:** Syncs the obsidian-claude framework (scripts, templates, rules) to the git repository and commits/pushes changes. Run after updating core framework files.

---

### `/update-config`
**What it does:** Configures Claude Code via `settings.json`. Use for: automated behaviors ("whenever X, do Y" → hooks), permissions ("allow npm commands"), environment variables, or troubleshooting hooks.

**Note:** Behavioral automations require hooks in settings.json — memory/preferences cannot enforce them (the harness executes hooks, not Claude).

---

### `/keybindings-help`
**What it does:** Customizes keyboard shortcuts — rebind keys, add chord bindings, modify `~/.claude/keybindings.json`.

---

### `/fewer-permission-prompts`
**What it does:** Scans transcripts for common read-only Bash and MCP tool calls, then adds a prioritized allowlist to `.claude/settings.json` to reduce permission prompts.

---

### `/run`
**What it does:** Launches and drives the project's app to verify a change works in the real app. Looks for a project-specific launch skill first, then falls back to built-in patterns (CLI, server, TUI, Electron, browser-driven, library).

---

### `/init`
**What it does:** Initializes a Claude Code project — creates CLAUDE.md, sets up settings, configures hooks for the current repo.

---

## Code Quality

### `/code-review`
**What it does:** Reviews a diff, PR number, branch, or path for correctness bugs, reuse/simplification, and efficiency cleanups. Can post findings as inline PR comments (`--comment`) or apply fixes (`--fix`).

**Effort levels:** low / medium / high / max

---

### `/simplify`
**What it does:** Reviews changed code specifically for reuse, simplification, efficiency, and altitude cleanups. Applies fixes. Quality-only — does not hunt for bugs (use `/code-review` for that).

---

### `/security-review`
**What it does:** Reviews code or infrastructure config for security vulnerabilities — OWASP Top 10, secrets scanning, cloud misconfigurations.

---

## Content & Presentations

### `/generate-pptx`
**What it does:** Two-step briefing workflow for presentations. Step 1: generates a Presentation Briefing from source material using the template at `~/Documents/IONOS-Obsidian/Templates/Presentation-Briefing.md`. Step 2 (on user confirmation): generates the `.pptx` from the IONOS template at `~/Documents/IONOS-Obsidian/104 - Claude/IONOS-Cloud-Template.pptx`.

**Key rule from CLAUDE.md:** Generate markdown for Gemini/Google AI Studio instead of python-pptx. Always start from `IONOS-Cloud-Template.pptx` (51 layouts, 53 example slides).

---

### `/excalidraw`
**What it does:** Creates or edits Excalidraw diagrams. Outputs `.excalidraw` JSON files compatible with Obsidian Excalidraw plugin.

---

## Superpowers Framework

The Superpowers plugin provides process discipline skills. Invoke **before** implementation tasks, not after.

| Skill | When to use |
|---|---|
| `/superpowers:brainstorming` | Before ANY creative/feature work — explore intent and requirements first |
| `/superpowers:systematic-debugging` | Before debugging any bug — establish hypothesis-driven approach |
| `/superpowers:writing-plans` | Before implementation — write a detailed spec |
| `/superpowers:executing-plans` | When executing a multi-task plan with subagents |
| `/superpowers:verification-before-completion` | Before marking any task done — prove it works |
| `/superpowers:test-driven-development` | Before writing implementation code |
| `/superpowers:requesting-code-review` | After implementation, before merging |
| `/superpowers:receiving-code-review` | When a code review comes back with findings |
| `/superpowers:finishing-a-development-branch` | Before closing/merging a branch |
| `/superpowers:subagent-driven-development` | When fanning out work to parallel subagents |
| `/superpowers:using-git-worktrees` | When starting an isolated code task |
| `/superpowers:writing-skills` | Before creating or editing a skill file |
| `/superpowers:dispatching-parallel-agents` | When running multiple independent research/analysis agents |
| `/superpowers:diagnosing-superpowers` | When a skill isn't working as expected |

---

## JIRA Projects Reference

| Project | Purpose | Notes |
|---|---|---|
| PCPM | PM work tracking | Every 101-Task needs a PCPM ticket |
| TWT | Technical Writing Team docs | Link back to parent PCPM ticket |
| PSC | Engineering delivery | Tinashe = PSC team lead |
| PAP | Website price calculator | For pricing page updates |
| TECCM | Change management | Migration dates, Change L = customer agreement |
| PROJECTS | PMO initiatives | Separate from PCPM; `PROJECTS-####` format |

**PCPM Parent Epics:**
- `PCPM-630` — All MK8s work
- `PCPM-871` — DBaaS roadmap (26 feature requests)
- `PCPM-720` — AI Studio / TWT umbrella

**Key rule:** Never write to JIRA via API — deliver paste-ready JIRA-wiki-markup blocks and let Ricardo create/edit tickets manually.

---

## Number & Currency Formatting Rule

Always use **European formatting**:
- Decimal separator: comma — `€1,50`
- Thousands separator: period — `€1.000`
- Combined: `€78.414,07`

In JavaScript: `value.toLocaleString('de-DE', { minimumFractionDigits: 2 })`

---

## Key People

| Name | Role |
|---|---|
| Ricardo de Larrea | PM (MK8s, DBaaS, PCR, AI Studio, Kafka) |
| Tinashe | MK8s Engineering Lead (PSC team) |
| Dimple Poojary | TWT contact for docs |
| Marie Funke | Legal / Public Sector (ITZBund) |
| Javier Saenz / Eckehard Kutzner | DBaaS Engineering |

---

## Active Projects Quick Reference (as of October 2026)

| Project | PCPM | Status |
|---|---|---|
| MK8s Maintenance Capacity Buffer | PRJ-IONOS-030, PCPM-802 | In progress |
| MK8s Private/Public Clusters | PRJ-IONOS-038 | Research |
| MK8s cpc-0 Migration Sales Briefing | T-IONOS-214, PCPM-940 area | Active |
| DBaaS PostgreSQL v1→v2 Storage Migration | — | Active (fee increase) |
| DBaaS Roadmap Q4 2026–Q4 2027 | PRJ-IONOS-037, PCPM-871 | Planning |
| DBaaS MongoDB v2 Launch | PCPM-859, PCPM-860 | Launched 2026-10-01 |
| MK8s Provisioning Benchmark | PRJ-IONOS-027 | Monthly cadence |
| Hermes Agent on MK8s | — | Live |
| ITZBund Tender (PROJECTS-2351) | PCPM-875, PSC-5777 | Ongoing |
| PM Portfolio Dashboard | — | `~/Coding/product-dashboard/` |
| Kafka 4.0 SACOM | PCPM-940 | Pending eng sign-off |
| create-pcpm-ticket Skill | — | Built 2026-10-01 |

---

*Last updated: 2026-10-02. Copy to `~/Documents/IONOS-Obsidian/900 - Permanent Notes/901 - IONOS Permanent Notes/P-20261002-claude-code-skills-reference.md`*
