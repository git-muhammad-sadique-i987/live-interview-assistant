---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** Framework only. Real experience at the bottom.

# Architectural Framing, Trade-offs and ADRs

This note exists because of a common gap: a lead or architect role wants someone who is **not just a
doer**, someone who brings reference designs, guardrails, and pragmatic trade-offs on cost, resilience
and security, while the natural instinct under interview pressure is to answer at command-line altitude.

Same knowledge, wrong altitude, reads as mid-level.

## The altitude rule

Name the **checkpoint, not the flag**. Name the **category, not the vendor** — unless asked, or unless
the job description names the product.

- Doer: *"I'd check `%us` versus `%sy` in `top`, then `iostat -xz 1` for I/O wait."*
- Lead: *"I'd establish whether it's compute, memory, I/O or network-bound before touching anything —
  that determines which team owns the next step."*

The second answer contains the first. If the interviewer wants the commands, they will ask, and then
you give them — that is a *stronger* sequence than volunteering them, because it shows you can
calibrate depth to the audience.

## The three trade-off axes

Almost every infrastructure decision is a trade between **cost, resilience, and security** (with
delivery speed as a frequent fourth). A lead-level answer names the trade explicitly rather than
presenting one option as simply correct:

> "You can get the RPO down to minutes, but that means continuous replication and roughly double the
> storage spend. Whether that's worth it depends on what an hour of data loss actually costs this
> business — which is a conversation with the service owner, not a decision I'd make unilaterally."

That framing does three things at once: it demonstrates the technical option, it shows cost
awareness, and it puts the decision with the right owner.

## Artefacts a lead is expected to produce

- **Reference architecture** — the standard pattern others build against, so each team is not
  inventing its own landing zone
- **Guardrails** — policy that makes the wrong thing hard rather than forbidden by memo
- **ADR (Architecture Decision Record)** — a short document per significant decision: context, the
  options considered, the decision, and the consequences accepted. The value is that the *reasoning*
  survives after the people leave
- **Standards** — naming, tagging, environment separation, logging — the boring things that make an
  estate governable
- **Runbooks** — so a responder is not improvising at 3am

## The uplift dimension

Lead roles often include mentoring and uplifting an existing team, for example an on-prem team moving
to cloud. When the job description says so, answers that acknowledge it score better:

> "I'd codify that as a pattern and run a session on it rather than just implementing it myself —
> the team already has deep on-prem depth, and the gap is cloud-native patterns, not capability."

## Framing to reach for

| Instead of | Say |
|---|---|
| "I'd fix it" | "I'd establish who owns it and what the constraint is" |
| "The best option is X" | "X trades cost for resilience; whether that's right depends on…" |
| "I'd script that" | "I'd make it a standard change so it's repeatable and doesn't need me" |
| "We used Terraform" | "We codified it so environments were reproducible — Terraform in that case" |

## The honest caveat that buys room

A line worth having ready, because it converts "I don't know your environment" from a weakness into
judgement:

> "I'd want to understand the actual production environment before proposing anything specific — but
> these are the priorities I'd establish first, in this order."

That is a complete answer. It does not hedge, it does not bluff, and it invites the interviewer to
give you the constraints so you can be concrete.

## My experience

<!-- Fill in yourself. Candidates:
     - Any reference design, standard, or ADR you actually wrote
     - A trade-off you actually made and what drove it
     - A time you chose the boring, governable option over the clever one
     - Mentoring or knowledge-sharing you actually did
     Delete this comment once written; omit the section if you have nothing real here. -->
