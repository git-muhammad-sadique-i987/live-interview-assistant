---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** Framework only. Real experience at the bottom.

# Stateless vs Stateful — the Recovery Decision

The single question that most changes the answer to any "how would you recover this?" scenario. Ask
it before proposing anything.

## The distinction

**Stateless** — the component keeps no memory of previous interactions. Any instance can serve any
request. A web tier using JWTs holds no server-side session, so any node can validate any token.

**Stateful** — the component *is* the memory. A database, a file server, a domain controller, an
identity store. Losing it loses something that cannot be regenerated.

## Cattle vs pets

The shorthand: stateless components are **cattle** — interchangeable, replaceable, and the correct
response to a sick one is to destroy it and spin up a replacement. Stateful components are **pets** —
individually valuable, and you nurse them back.

The mistake is treating everything as a pet. Rebuilding a stateless node from a known-good image is
usually faster than diagnosing it, and it is *categorically safer* after a compromise, because you
are not trying to prove that a running system is clean.

## Why this matters after a security incident

For a compromised **stateless** node, the recovery is a rebuild. You do not need a backup, you do not
need to establish whether the backup predates the dwell time, and you do not need to prove the system
is clean — you replaced it with something known good. Fast and defensible.

For a compromised **stateful** system, none of that applies. You need a validated clean recovery
point, you have an RPO conversation about acceptable data loss, and you may need forensics on the
original before it is destroyed.

**Caveat worth stating:** "stateless" is a design property, not an assumption. A web server that
keeps local session state, uploaded files on local disk, or a local cache that other things depend on
is not actually cattle no matter what the architecture diagram says. Verifying that is part of the
answer.

## How this shapes the scoping question

> "Before I'd give you a recovery time, I'd want to know whether this is a stateless tier or a
> stateful one. If it's a web front end behind a load balancer holding no session state, I'd rebuild
> from a known-good image rather than restore — faster, and it removes the question of whether a
> backup predates the compromise. If it's a database, that's a different conversation and RTO/RPO
> drive it."

That single move demonstrates architectural thinking, avoids committing to a number you were not
given the inputs for, and invites the interviewer to give you more.

## Related design consequences

- Stateless tiers can scale horizontally and be replaced during business hours; stateful ones usually
  need a maintenance window
- Statelessness is what makes autoscaling and blue/green deployment viable
- Pushing state *out* of a tier — to a shared cache, a managed database, object storage — is often the
  architectural fix that makes future recovery trivial. That framing suits a lead-level role: the
  answer is not just how to recover, but how to make recovery boring next time.

## My experience

<!-- Fill in yourself. Candidates:
     - Systems you've actually operated and whether they were stateless or not
     - A time you rebuilt rather than repaired, and why
     - Any migration you did that moved state out of a tier
     Delete this comment once written; omit the section if you have nothing real here. -->
