---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** Framework only. Real experience at the bottom.

# RTO, RPO, and Ransomware Recovery

The scoping vocabulary for "a server was hit by ransomware — how do you get it back and how long
will it take?" This question cannot be answered cold, and the questions you ask before answering are
most of the signal.

## The two objectives

- **RPO — Recovery Point Objective.** The maximum acceptable *data loss*, expressed in time. Set by
  how far back the last usable recovery point sits.
- **RTO — Recovery Time Objective.** The maximum acceptable *downtime* before the disruption becomes
  severe.

Both are business decisions, not technical ones. Leadership determines acceptable downtime and data
loss based on risk tolerance; IT provides the technical implementation to meet them. Saying that out
loud is itself a seniority signal.

They are also only real if tested — targets should be validated with an end-to-end recovery including
dependencies, then adjusted to what is both required and achievable.

## Why ransomware breaks naive backup assumptions

The critical asymmetry: **attackers dwell in the environment before detonating.** By the time
encryption is detected, multiple backup cycles may already be compromised, and attackers frequently
target backup infrastructure *first* to eliminate recovery options. Many organisations with backups
still fail to restore in a real attack.

So the question is never "do you have backups?" It is:

1. Are the backups **immutable** — unable to be modified, encrypted, or deleted once written, even by
   an administrator with elevated privileges?
2. Are they **isolated** or off-site, so ransomware cannot reach them from production?
3. Can you **identify a clean, validated recovery point** from before the dwell period began?
4. Is there an **isolated recovery environment** to restore into and scan before reconnecting?

Without immutability and validation, an RPO number is guesswork.

## Controls that make recovery defensible

- Immutable / locked recovery points, plus soft delete, so purging is impossible within the retention
  window even after credential theft
- Separation of duties between backup operators and workload admins
- MFA on backup and recovery systems, and backup admin accounts separate from normal domain accounts
- Multiple recovery points per day rather than a single nightly backup, so the RPO is not "up to 24
  hours"
- Documented approval for who can authorise a restore
- Scan restored systems before reconnecting; rotate credentials during recovery

## The decision that actually drives the answer

**What kind of workload is it?** This changes everything and is the first thing to ask:

- A **stateless** component — a web front end holding no session state — can often be rebuilt from a
  known-good image rather than restored. Faster, and it sidesteps the "is this backup clean?"
  question entirely.
- A **stateful** system — a database, a file server, an identity store — must be restored, and the
  RPO conversation is unavoidable.

See also: `REF-Stateless-vs-Stateful-Recovery`.

## Scoping questions for this scenario

Ask two or three of these before proposing anything:

- Is the affected system a web tier, an application server, or a database?
- What is the RTO and RPO for this workload specifically?
- Do you have immutable or off-site snapshots, and what is the retention window?
- When was the compromise first detected, and do we have any sense of the dwell time?
- Is there an isolated environment I can restore into and validate before reconnecting?
- What is the smallest useful business function we could restore first? *(Staged recovery beats
  all-or-nothing.)*
- Is this also a notification/compliance event, and who owns that?

## Shape of a good answer

1. Establish what the workload is and whether it is stateful.
2. Establish the RTO/RPO and whether clean recovery points exist.
3. Separate containment from recovery — stop the spread before restoring, or you restore into a
   compromised environment.
4. Prefer staged recovery of the most critical function first.
5. Note that forensics may need to happen in parallel, and it is often a legal/compliance event as
   well as a technical one.

## My experience

<!-- Fill in yourself. Candidates:
     - Any backup/DR platform you actually operated, and what its real recovery times were
     - A restore you actually performed, and what went wrong
     - Whether you've ever tested a DR plan end-to-end, and what the test revealed
     - Any security incident you were involved in, and what your role was
     Delete this comment once written; omit the section if you have nothing real here.
     Do NOT claim ransomware recovery experience you don't have — this is exactly the topic where an
     interviewer will drill in. -->
