---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** Framework only. Real experience goes at the bottom.

# Severity, Priority, and Escalation

The scoping vocabulary for "how bad is this, and who do I wake up?" Useful because it lets you answer
a vague scenario question with a *classification* before committing to a solution.

## Severity vs priority — keep them separate

- **Severity** = how bad the impact is. Objective, customer-facing.
- **Priority** = the order you will actually work on it. Combines severity with effort, dependencies,
  and timing.

Two incidents at the same severity may not carry the same priority. A SEV2 affecting a major
customer mid-launch outranks a SEV2 in a test environment. Priority is judgement in the moment;
severity is classification.

When these blur, triage breaks: low-severity/high-urgency issues get ignored, and
high-severity/low-urgency issues pull in too many people too fast.

## Severity is derived from two independent axes

- **Impact** — how broadly and deeply users or business operations are affected. How many users? Is
  core functionality down or degraded? Is there a security or data risk?
- **Urgency** — how fast it will worsen without intervention. Is it spreading? Is a workaround
  available?

Assess each separately, *then* combine. The practical value of the matrix is in forcing that
separation before the label is applied.

## A typical scale

| Level | Rough definition | Response shape |
|---|---|---|
| SEV0/1 | Complete outage or security breach, no workaround | Immediate page, IC assigned, exec notification, 15-min update cadence, mandatory postmortem |
| SEV2 | Major degradation, significant business impact | Page on-call, escalate to lead if unresolved, 30-min updates, postmortem expected |
| SEV3 | Partial or limited degradation | Ticketed, business-hours triage, no paging unless it escalates |
| SEV4 | Minor / cosmetic | Backlog, reviewed in weekly triage |

Labels vary (SEV1–5, P0–P3, critical/major/minor); the structure does not. Most organisations land on
four or five levels.

## Rules that signal experience

- **Err high during a live incident.** Over-escalating one incident costs less than under-escalating
  and letting impact compound. Calibrate down in the postmortem.
- **Watch for severity inflation.** If 30%+ of incidents are classified top-tier, the label has lost
  its meaning and on-call burns out.
- **Auto-escalate on duration.** A SEV2 unresolved past a threshold should trigger a SEV1 review.
  Anything spreading to new systems warrants reclassification.
- **Severity reflects potential impact, not duration.** Fixing it fast does not retroactively make it
  a lower severity.
- **If two severity levels have the same paging, response time, and review expectation, they are one
  level with two names.** Merge or differentiate them.
- Reclassification in the postmortem is about data accuracy, not blame — and MTTA/MTTR are only
  meaningful when sorted against correct severity.

## Escalation should be codified, not tribal

Each level needs a defined escalation policy: who is paged first, who is the backup, and at what
point it goes to leadership. Codified in tooling rather than in someone's memory, so response is
predictable when the person who knows is on holiday.

## Using this in an answer

For a vague scenario question, classification *is* a legitimate first move:

> "Before I'd commit to an approach I'd want to establish impact and urgency separately — how many
> users, whether it's spreading, and whether there's a workaround available. That drives the severity,
> and severity drives who gets engaged and how often we communicate."

That answers the question without pretending to know facts you were not given.

## My experience

<!-- Fill in yourself. Candidates:
     - What severity/priority scheme your organisation actually used
     - An incident you classified, and whether the classification held up in review
     - How escalation actually worked (or failed) in practice
     - Any on-call rotation you were part of and what the paging thresholds were
     Delete this comment once written; omit the section if you have nothing real here. -->
