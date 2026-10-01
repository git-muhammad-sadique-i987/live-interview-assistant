---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** Framework only. Real experience at the bottom.

# Change Management, CAB and ECAB

Answers the unspoken question behind every "how would you fix this?" — *could you actually make that
change right now, and who authorises it?* Mentioning this is what separates a lead's answer from a
technician's.

## What counts as a change

The addition, modification, or removal of anything that could affect an IT service. Scope includes
architectures, processes, tools, metrics, and documentation — not just servers.

## The three change types

**Standard change** — pre-approved, low risk, fully documented with work instructions, implemented
without additional authorisation. Ideally automated. A proven history of not causing incidents is
what earns something this classification.

**Normal change** — goes to the **Change Advisory Board (CAB)** for authorisation. Degree of scrutiny
scales with scope, risk, and priority. The Change Manager usually chairs the CAB.

**Emergency change** — expedited assessment and authorisation via the **Emergency CAB (ECAB)**, to
ensure speed. Important nuance: as far as possible, emergency changes should still be subject to the
same testing, assessment, and authorisation as normal changes — the ECAB compresses the timeline, it
does not remove the controls.

The point of getting standard changes pre-approved and automated, and emergency changes fast-tracked,
is so the CAB's attention is spent on normal changes where the judgement is actually needed.

## Why this belongs in incident answers

Restoring service usually *is* a change. So a complete answer acknowledges the authorisation path:

> "The rollback itself is an emergency change — I'd raise it as such and get ECAB approval in
> parallel with preparing it, rather than either skipping the process or waiting on a full CAB cycle
> while the business is down."

That demonstrates you can move fast *within* governance rather than around it, which is exactly what
a lead-level infrastructure role is being hired to do.

## The permanent fix is a separate change

A pattern worth repeating: the workaround is an emergency change during the incident; the permanent
fix comes out of problem management and goes through normal change with proper testing. Two changes,
two authorisation paths, two timelines. Collapsing them is how outages get caused by their own fixes.

## Related governance vocabulary

- **RFC** — Request for Change, the formal record
- **Change window / freeze** — approved implementation periods, and blackout periods around
  business-critical events
- **Backout plan** — the "if this goes wrong, how do we undo it" section. A change without one should
  not be approved
- **Post-implementation review** — did the change do what it claimed, without side effects
- **Configuration drift** — the gap between documented and actual state; the thing change control
  exists to prevent

## My experience

<!-- Fill in yourself. Candidates:
     - Whether your organisation actually ran a CAB, and how heavy it was in practice
     - An emergency change you raised, and what the approval actually looked like
     - A change that went wrong and how the backout plan performed
     - Any drift-detection or config-management tooling you actually operated
     Delete this comment once written; omit the section if you have nothing real here. -->
