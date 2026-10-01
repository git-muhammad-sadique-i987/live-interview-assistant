# Reference: incident severity levels

Framework reference, not a record of experience. A common severity scheme, roughly as used across the
industry.

| Severity | Meaning | Typical response |
|---|---|---|
| SEV1 | Complete outage or data loss affecting all or most users | Immediate page, incident commander, executive communication, all hands available |
| SEV2 | Major functionality degraded, or a subset of users fully affected | Immediate page, incident process, stakeholder updates |
| SEV3 | Partial degradation with a workaround, limited user impact | Business-hours response, tracked to resolution |
| SEV4 | Minor issue, cosmetic, or affecting internal tooling only | Normal backlog |

## Severity is not priority

Severity describes impact; priority describes the order of work. They usually correlate and are
allowed to diverge - a SEV3 affecting the single customer in a contract renewal may be worked before
a SEV2 affecting an internal tool.

## Rules that make the scheme work

- **Declare high and downgrade.** Downgrading is cheap; discovering forty minutes in that it was
  always a SEV1 is not.
- **Anyone may declare.** A scheme where only senior engineers can call an incident delays every
  incident by the time it takes to find one.
- **Severity is about impact, not cause.** A configuration typo and a hardware failure with the same
  user impact are the same severity.
- **Time-based escalation.** A SEV2 unresolved after an agreed duration becomes a SEV1 automatically,
  so the decision to escalate does not depend on tired judgement.
