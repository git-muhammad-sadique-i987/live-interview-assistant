---
type: reference
tier: reference
status: framework-only
experience: none-yet
---

> **REFERENCE NOTE — not my hands-on experience.** A question bank, not a claim about anything I have
> done.

# Scoping Questions — What to Ask Before Answering

Asking two or three well-chosen clarifying questions before proposing anything is one of the
strongest signals available in a technical interview. Hiring managers report candidates moving from
"maybe" to "strong yes" on the strength of the questions alone — because most candidates jump
straight to solutions without understanding the constraints.

Two rules:

1. **Two or three, not five.** More than that reads as stalling or as an inability to proceed under
   ambiguity.
2. **Not for lookup questions.** *"What's the Azure equivalent of a security group?"* gets the answer,
   immediately. Scoping a factual question looks like you don't know it.

## By scenario type

### Outage / degradation

- How many users are affected, and is it degrading or stable?
- Is there a workaround currently in place?
- When did it start, and does that correlate with a change or a deployment?
- Is this a single instance or estate-wide?
- What is the business impact — revenue, safety, compliance, or inconvenience?

### Recovery / disaster / ransomware

- Is this a stateless tier or a stateful system?
- What is the RTO and RPO for this specific workload?
- Do immutable or off-site recovery points exist, and what is the retention window?
- When was the compromise detected, and what do we know about dwell time?
- What is the smallest useful business function to restore first?

### Performance

- Is this a new problem or has it been gradual?
- Is it affecting all users or a subset — by region, by tenant, by client type?
- What changed recently — deployment, config, data volume, user growth?
- What does "slow" mean here — is there an SLO it is breaching?

### Capacity / cost

- What is the growth trajectory we are designing for?
- Is the constraint budget, or is it a technical ceiling?
- Is this steady-state load or spiky?

### Security

- Is this contained, or still active?
- Has the blast radius been established — what identities and systems were reachable?
- Is this a notification or compliance event as well as a technical one?
- Who owns the forensics, and do we need to preserve evidence before remediating?

### Design / architecture

- What is the availability target, and what is the tolerance for cost against it?
- Is this greenfield or does it have to interoperate with existing on-prem?
- Who operates this once it is built, and what is their current skill level?
- Are there compliance or data-residency constraints?

### Migration

- Is there a hard deadline, and what is driving it?
- Can we tolerate a cutover window, or does it need to be live?
- What is the rollback plan if the cutover fails?

## The universal three

If nothing else fits, these almost always apply:

1. **What is the actual business impact?** (drives priority)
2. **What changed?** (drives diagnosis)
3. **Who owns this, and who can authorise a change to it?** (drives what you can actually do)

## Framing so it doesn't sound evasive

- "Before I commit to an approach, two things would change my answer significantly —"
- "That depends on one thing: is it stateful or stateless?"
- "I can give you the general shape now, but the specifics hinge on X — which way is it?"

The failure mode to avoid is asking questions *instead* of demonstrating knowledge. The strong
pattern is: ask two, then answer with the general shape anyway, noting how the answer would change
under each branch.

## What the interviewer is testing

They are usually checking whether you treat the exchange as a collaboration or as an exam. A nudge
like *"what about consistency here?"* is not a gotcha — it is an invitation to discuss a trade-off.
Candidates who respond defensively score lower even when the technical content is correct.
