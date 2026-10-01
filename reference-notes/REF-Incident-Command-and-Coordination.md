---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** Framework vocabulary only. My own experience goes
> in the section at the bottom, and only if I have actually done it.

# Incident Command and Cross-Team Coordination

This is the formal vocabulary for "most problems get resolved between teams, not by one admin."
Saying *"I'd have a meeting with the application team"* is the vague version. This is the version
that sounds like someone who has run a major incident.

## The three core roles (Google's IMAG / Incident Command System)

**Incident Commander (IC)** — the single accountable decision-maker. Coordinates the response,
delegates roles, sets priorities, keeps situational awareness of what has been tried and what is
working. By default the IC holds every role that has not yet been delegated. Critically, **the IC
should not be modifying systems** during the incident.

**Operations Lead (OL)** — applies the actual technical remediation. This is the person with hands on
keyboard.

**Communications Lead (CL)** — the information hub. Regular, rhythmic updates to stakeholders,
leadership, and where relevant customers or a status page. Exists specifically so the OL is not
interrupted every ten minutes to explain progress.

Larger responses add a **Scribe** (documentation) and a **Liaison** (external parties, vendors).

## Rules worth quoting

- **Do not dual-hat the Incident Commander and the Technical Lead.** Below roughly 8 engineers one
  person can cover both; above that, combining them creates cognitive overload and extends
  resolution time.
- Whoever declares the incident typically becomes IC by default, and hands off later if someone more
  senior arrives.
- The IC owns an **Incident Action Plan**: current objectives, what has been tried, next steps. Kept
  short, current, and visible. Refreshed on a defined cadence — 30–60 minutes for a major incident.
- The IC has the authority to pause a deploy or revert a change if conditions look unsafe.
- The IC owns making sure the postmortem actually happens *and* that its actions get done.

## Why this matters in an interview

The interviewer is often testing whether you understand that a lead's job during a crisis is
coordination, not heroics. An answer that ends *"...and I'd hand the app team the Ops Lead role while
I stay on coordination and comms"* demonstrates that. An answer that ends *"I'd kill the process"*
demonstrates the opposite.

## RACI — for non-incident cross-team work

For projects, changes, and standing processes rather than live incidents:

- **R**esponsible — does the work
- **A**ccountable — answerable for the outcome; **exactly one per row**
- **C**onsulted — two-way input before the decision
- **I**nformed — told after the fact

Practical rules: exactly one A per row and at least one R; keep C and I to the critical few, because
excessive consultation slows everything down; use role names rather than people's names so the matrix
survives staffing changes; tie the A to the approving body where one exists (e.g. the Change Advisory
Board).

Its main value is in matrixed organisations — the failure it prevents is duplicated effort,
bottlenecks, and last-minute escalations.

## The coordination move, generalised

Almost any "how would you fix X" scenario has a coordination answer sitting behind the technical one:

- Who owns the affected service, and are they engaged?
- Who is authorised to approve the change I am about to propose?
- Who needs to be told, and how often?
- Who takes it after I hand off — and what do they need from me?

## My experience

<!-- Fill in yourself. Only what actually happened. Candidates:
     - An incident where you coordinated across teams, and what your actual role was
     - How your organisation handled comms during an outage (status page? bridge call? Teams channel?)
     - A time coordination, rather than a technical fix, was the thing that resolved it
     - Any RACI or ownership matrix you actually built or worked to
     Delete this comment once written; omit the section entirely if you have nothing real here. -->
