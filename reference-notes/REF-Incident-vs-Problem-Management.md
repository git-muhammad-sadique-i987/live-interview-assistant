---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** This is domain framework knowledge for
> vocabulary and structure. Anything I claim as *mine* goes in the "My experience" section at the
> bottom, and only after I have actually done it.

# Incident vs Problem Management

The single most useful distinction for answering "the server is down, what do you do?" questions.
Most candidates conflate the two and jump straight to root cause. Senior answers separate them.

## The split

**Incident management — restore service.** The objective is speed. An incident is any unplanned
interruption or reduction in quality of an IT service. Success is measured by service restoration,
*not* by root cause elimination. A restart, a failover, a traffic reroute, a config rollback are all
legitimate incident resolutions.

**Problem management — remove the cause.** Operates in investigation mode, not real time. Triggered
by a pattern of recurring incidents with a shared failure signature, or by a single major incident
severe enough to warrant investigation regardless of frequency. A problem is the cause, or potential
cause, of one or more incidents.

**The rule that matters:** root cause analysis must not delay service restoration. RCA belongs to
problem management.

## Why this is the answer to "should we give them a temporary fix?"

Yes — and naming it correctly is the seniority signal. Restoring service via workaround while
investigation continues is not a shortcut or an admission of defeat. It is the defined process.

A team that restores service in eighteen minutes has performed well by incident management
standards. A team that restores in eighteen minutes and hits the identical failure three weeks later
has only deferred the cost. Speed without pattern recognition is operational repetition, not
operational maturity. Both processes are needed; they are not alternatives.

## Vocabulary worth using out loud

| Term | Meaning |
|---|---|
| **Workaround** | A temporary measure that restores service without addressing the cause |
| **Known error** | A problem with a documented root cause and/or a workaround on record |
| **Incident record** | The ticket tracking a single disruption |
| **Problem record** | The investigation tracking the underlying cause |
| **RCA** | Root cause analysis — a problem-management activity, not an incident one |
| **PIR / postmortem** | Post-incident review, after service is restored |

## Who typically owns what

Incident management sits with the service desk and Tier 1 support, focused on restoration. Problem
management sits with Tier 2/Tier 3 specialists or SREs who investigate causes. In smaller teams one
person wears both hats — but they are still two different activities with different success criteria,
and saying so explicitly is what sounds senior.

## Worked example

Email stops working for 200 users.

- **Incident:** reroute traffic, restart the service, or fail over to a secondary system. Service is
  back. Incident closed.
- **Problem:** the outage happened because a certificate expired or a load balancer rule was
  misconfigured. Problem management investigates and puts a permanent fix in place — plus, ideally,
  monitoring so it is caught before it bites again.

## How I would frame this in an answer

The shape, not the script:

1. Establish impact and urgency first — how many users, is it degrading further, is there a
   workaround.
2. State plainly that the first objective is restoring service, and name the candidate workarounds.
3. Separate that from the investigation, and say who owns it.
4. Note that the permanent fix goes through change management, not straight into production.

Avoid: leading with the diagnostic commands. That is the doer's answer, and it invites interrogation
on flags and syntax rather than on judgement.

## My experience

<!-- Fill this in yourself. Only what you have actually done. Examples of what belongs here:
     - A time you chose a workaround over an immediate fix, and what drove the decision
     - An incident where RCA was deliberately deferred, and who agreed to that
     - A recurring incident you converted into a problem record
     - What your ticketing/ITSM tooling actually was, and how the process worked in practice
     Delete this comment block once written. If you have no experience here, leave the section out
     entirely rather than inventing one — the app is designed to say so honestly. -->
