# MK8s Maintenance Scenario Explorer — Design Spec

**Date:** 2026-04-23
**Author:** Ricardo de la Rrea Remiro
**Status:** Draft
**Target audience:** Felix (Product Director, MK8s)
**Decision to support:** Approve engineering investment for capacity-aware maintenance scheduling

---

## 1. Purpose

An interactive, single-file HTML wizard that walks a product director through the MK8s maintenance capacity problem, presents three solution directions with trade-offs, and lets the viewer explore custom alternatives using an optional AI layer (Anthropic Claude API).

The goal is not a slide deck Felix passively watches — it's a **decision support tool** he actively engages with.

---

## 2. Problem Context

### The situation

- 2.000 MK8s clusters on the IONOS platform
- 80% of customers choose weekend maintenance windows
- Maintenance uses an n+1 node replacement pattern (new node created before old node removed)
- 1.600 clusters competing for capacity on Saturday/Sunday nights
- Buffer capacity kept intentionally small to control server costs
- When buffer is exhausted → maintenance aborted mid-process → inconsistent cluster state
- 10-20 incidents every Monday morning requiring manual cleanup
- ~780 incidents/year, ~585 ops hours/year (0,34 FTE equivalent)

### Root cause

The problem is demand concentration, not insufficient capacity. Spreading 1.600 weekend clusters across 7 days reduces peak demand by 5.6×. The current buffer that fails on weekends would be more than sufficient if load were distributed.

### Felix's constraint

Same server budget, fewer incidents. No additional capacity spend. Open to any approach that meets this constraint.

---

## 3. Product: Interactive Scenario Explorer

### 3.1 Format

- **Single self-contained HTML file** — no build tools, no npm, no server required
- Felix opens it in any browser, works offline (except AI features)
- Google Fonts loaded for Overpass + Open Sans, system sans-serif fallback if offline
- All data hardcoded as JS constants at the top of the file (editable before sharing)

### 3.2 Visual Design

**Theme:** Light, IONOS brand

| Role | Color | Usage |
|---|---|---|
| Background | `#FFFFFF` | Page |
| Surface | `#F5F7FA` | Cards, panels |
| Primary | `#003D8F` | Headers, active states, key numbers |
| Dark navy | `#001B41` | Headings, strong text |
| Body text | `#718095` | Paragraphs |
| Muted | `#97A3B4` | Labels, secondary |
| Accent | `#FFAA00` | Recommendation highlight, selected states |
| Danger | `#E5342E` | Problem indicators, negative cells |
| Success | `#00875A` | Solution indicators, positive cells |

**Typography:** Overpass Bold for headings, Open Sans for body.

**Tone:** Clean, professional, generous white space. Cards with subtle `#E8ECF0` borders, no heavy shadows.

### 3.3 Wizard Flow (10 steps)

Navigation: Next/Back buttons at bottom, arrow keys + spacebar support. Progress bar at top. Step indicator top-right.

| Step | Title | Content | Interactive elements |
|---|---|---|---|
| 1 | "We have a maintenance problem." | 4 key stats (2.000 clusters, 80% weekend, 10-20 incidents, ~780/year) + framing paragraph | None — sets the scene |
| 2 | "Here's what happens every weekend." | 6-step cascading failure chain diagram | Hover tooltips on each step |
| 3 | "What this costs us." | Annual cost model | Slider: incidents/week (10-20) → dynamically recalculates annual incidents, ops hours, FTE |
| 4 | "The problem isn't capacity. It's concentration." | Bar chart: current demand distribution | Toggle switch: animate from concentrated → even distribution |
| 5 | Direction 1: Provider-Managed Distributed Scheduling | How it works, pros/cons, capacity impact chart | Expandable sections |
| 6 | Direction 2: Capacity-Aware Smart Scheduling (Recommended) | How it works, pros/cons, capacity impact chart | Expandable sections |
| 7 | Direction 3: Continuous Rolling Maintenance | How it works, pros/cons, capacity impact chart | Expandable sections |
| 8 | "See a different path?" | AI-powered custom direction generator | Text input → AI generates structured direction card (requires API key) |
| 9 | Comparison matrix | Side-by-side table across 9 dimensions | Dynamic — includes any custom directions from step 8 |
| 10 | Recommendation | Phased timeline + the ask | Print summary button |

### 3.4 Three Pre-Defined Directions

**Direction 1: Provider-Managed Distributed Scheduling**
- IONOS assigns maintenance slots, distributing clusters evenly across 7 days
- Customer defines blackout periods but doesn't pick the window
- 24-48h advance notification
- Pros: eliminates concentration, zero extra server cost, simplest engineering
- Cons: breaking change (customers lose window choice), needs notification infrastructure, migration risk

**Direction 2: Capacity-Aware Smart Scheduling (Recommended)**
- Customer keeps their chosen window
- System checks capacity before starting maintenance; if insufficient, queues and defers
- Priority queue: security patches first
- Staggered starts within the 4h window
- Pros: no customer-facing change, graceful degradation, incremental rollout, zero extra server cost, fully reversible
- Cons: doesn't solve root cause, some maintenance delayed, complex queueing logic, concentration worsens at scale

**Direction 3: Continuous Rolling Maintenance**
- No windows — maintenance happens continuously as capacity allows
- System monitors pending patches, starts when capacity available
- Customer gets post-completion notification + optional freeze toggle
- Pros: maximum capacity utilisation, zero waste, simplest customer UX, fastest patch delivery
- Cons: biggest departure from current model, regulated customers need freeze capability, business-hours surprises

### 3.5 AI-Powered Custom Directions (Step 8)

**Activation:** Felix enters an Anthropic API key in a settings drawer (gear icon, top-left). Key stored in `localStorage` only, never leaves the browser except to the Anthropic API endpoint.

**Privacy notice displayed:** "Your API key stays in your browser. Questions are sent directly to Anthropic's API — not through any IONOS or third-party server."

**System prompt:** Pre-loaded with full problem context:
- All data points (2.000 clusters, 80% weekend, n+1 pattern, 10-20 incidents, buffer constraints)
- All three pre-defined directions with pros/cons
- Competitive analysis summary (DOKS, OVHCloud, STACKIT, OTC approaches)
- Felix's constraint (same server budget, fewer incidents)
- Output schema: JSON with name, description, how_it_works (array), pros (array), cons (array), capacity_impact (string), engineering_effort (string), time_to_value (string), customer_impact (string)

**Interaction:**
- Felix types a question or describes an alternative approach
- AI responds with structured JSON matching the direction schema
- Wizard renders it as a new direction card (same visual style as directions 1-3)
- Felix can generate multiple custom directions
- Each custom direction gets a "Remove" button

**Per-step AI questions:** On every step (not just step 8), a small "Ask a question about this" input appears if the API key is set. Responses appear in an inline card below the question.

### 3.6 Persistence (localStorage)

| Data | Key | Persistence |
|---|---|---|
| Anthropic API key | `mk8s-api-key` | Survives browser restart |
| Custom directions | `mk8s-custom-directions` | Survives browser restart |
| Current step | `mk8s-current-step` | Resumes where Felix left off |
| Slider values | `mk8s-slider-values` | Remembers settings |
| Toggle states | `mk8s-toggle-states` | Remembers choices |

**Export:** Settings drawer includes an "Export session" button → downloads all state as a JSON file. Can be reimported in another browser or shared.

### 3.7 Comparison Matrix Dimensions

The comparison table evaluates each direction (3 fixed + N custom) across:

1. Additional server cost
2. Monday incidents eliminated (%)
3. Customer-facing change (none / breaking)
4. Engineering effort (small / medium / large)
5. Time to value
6. Customer communication needed
7. Solves root cause (yes / partially / no)
8. Long-term scalability
9. Rollback risk

Cells are colour-coded: green (win), amber (neutral), red (lose).

For custom directions, the AI generates the cell values as part of the structured response.

### 3.8 Recommendation (Step 10)

Phased timeline:
- **Phase 0 (Now):** Current state — 10-20 incidents/week
- **Phase 1 (Invest here):** Direction 2 — capacity-aware scheduling. 2-3 months, incremental, reversible.
- **Phase 2:** Notification infrastructure (from T-IONOS-140 Phase 1). Builds the communication layer needed for Phase 3.
- **Phase 3:** Structural change — Direction 1 or 3. Decision based on Phase 1 learnings + customer feedback.

If Felix generated a custom direction that scores well, the AI suggests how it fits into the phased timeline.

**The ask (highlighted in amber):** Approve engineering investment for Direction 2. 2-3 months to deploy. Zero additional server cost. ~90% incident reduction. No customer-facing change. Fully reversible.

---

## 4. Data Inputs (Configurable)

Hardcoded as JS constants at the top of the file. Ricardo adjusts before sharing.

```javascript
const CONFIG = {
  totalClusters: 2000,
  weekendPercentage: 0.80,
  incidentsPerWeekMin: 10,
  incidentsPerWeekMax: 20,
  incidentsPerWeekDefault: 15,
  avgCleanupMinutes: 45,
  fteHoursPerYear: 1716,
  weekendsPerYear: 52
};
```

---

## 5. Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Single HTML file | Yes | Felix opens it in any browser, no install, shareable via email/Slack |
| No build tools | Yes | No npm, no Vite — just HTML/CSS/JS |
| Anthropic API direct from browser | Yes | `fetch()` to `api.anthropic.com` with CORS. No backend proxy needed. |
| localStorage for persistence | Yes | Simplest. No accounts, no server. Export as safety net. |
| Google Fonts with fallback | Yes | IONOS brand fonts if online, system sans-serif if offline |
| Claude claude-sonnet-4-6 for AI queries | Yes | Fast, capable, cost-effective for follow-up questions |

---

## 6. Out of Scope

- Backend server or database
- User accounts or authentication
- Multi-user collaboration (Felix works solo, shares via export)
- Mobile-optimised layout (desktop-first for director presentation)
- Printing individual custom directions (print exports all steps)

---

## 7. Relationship to Existing Work

| Existing artifact | Relationship |
|---|---|
| T-IONOS-140 (Maintenance Policy & PM Playbook) | This tool presents the capacity problem that T-IONOS-140 Phase 1 partially addresses. The recommendation connects to T-IONOS-140's Phase 1 deliverables. |
| P-20260330 (Design spec) | The notification infrastructure from this design becomes Phase 2 of the scenario explorer's recommendation. |
| Rpt-IONOS-20260310 (Competitive analysis) | Data from this report is included in the AI system prompt for informed follow-up responses. |
| PRJ-IONOS-011 (Strategy workshop) | The scenario explorer could be used as a follow-up tool for workshop outcomes related to maintenance. |

---

## 8. Success Criteria

- [ ] Felix can navigate all 10 steps without confusion
- [ ] The argument builds progressively — each step is necessary context for the next
- [ ] The cost slider makes the problem tangible (not abstract)
- [ ] The distribution toggle creates the "aha moment" (same buffer works if spread)
- [ ] Custom directions generate correctly and appear in the comparison matrix
- [ ] Felix can resume where he left off after closing the browser
- [ ] The file works offline (minus AI features)
- [ ] The recommendation step provides a clear, specific ask
