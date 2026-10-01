---
tier: production
---

# On call and incident response

Six years of rotations, most recently as the person who runs the bridge on a major incident.

## Running an incident

- **Say out loud that it is an incident.** The ambiguous period where three people are quietly
  investigating and nobody has declared anything is where the time goes.
- **Separate the roles.** Someone coordinates, someone investigates, someone communicates outward. On
  a small team one person can hold two, but never coordination and deep investigation together - the
  moment you are head-down in a trace you have stopped coordinating.
- **Timestamps in the channel as you go.** What we saw, what we tried, what changed. Writing the
  timeline afterwards from memory produces a document that is wrong in the specific details that
  matter for the fix.
- **Mitigate before you diagnose.** Restore service first, understand it fully afterwards. Roll back,
  fail over, shed load - whatever ends the customer impact. The temptation to find root cause while
  users are down is strong and should be resisted.

## Communication

Stakeholders want three things: is it still happening, who is affected, and when will you next
update. A short update on a predictable interval beats a detailed one when you have a full answer,
because until you commit to an interval everyone keeps asking.

## Postmortems

We write them blameless and we write them for the incidents that were nearly bad as well as the ones
that were. The action items have owners and dates, and we review the open ones monthly - a postmortem
with no follow-through is theatre.

The most useful question I have found is not "what caused this" but "what made this take so long to
detect and so long to fix". Cause tends to be specific and unlikely to repeat. Detection and recovery
time are systemic and repeat constantly.

## What I would tell someone joining a rotation

Your first goal is not to fix things unaided. It is to know what normal looks like, where the
runbooks are, and who to escalate to without hesitating. The engineers who are good on call are the
ones who escalate early and without embarrassment.
