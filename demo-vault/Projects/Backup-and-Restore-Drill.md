---
tier: project
---

# Backup and restore drill

I ran a restore drill because I could not answer "when did we last test a restore" and the honest
answer was that nobody knew.

## How I ran it

Picked one production database and one file share, restored both to isolated infrastructure, and
timed everything from the decision to restore to the point where the restored copy was verifiably
usable. Nothing was touched in production; the point was to measure, not to prove bravery.

## What we found

- **The backups existed and were valid.** Genuinely good news and not a given.
- **The restore took nearly four times longer than anyone assumed.** Every plan in the wiki quoted a
  number that turned out to be someone's estimate from years earlier, and no one had ever measured
  it.
- **Two dependencies were missing entirely.** We backed up the database beautifully and did not back
  up the configuration required to bring the application up against it. On paper we could restore; in
  practice we would have restored a database nothing could talk to.
- **Documentation assumed knowledge the author had.** One step said to restore normally. The person
  who wrote it had left.

## What changed after

- The real measured RTO went into the recovery plan, replacing the guess.
- The missing configuration went into the backup scope.
- The runbook was rewritten by someone who had not done it before, following it literally, with the
  author watching and not helping.
- The drill went on the calendar twice a year.

## What I take from it

An untested backup is a belief, not a control. The drill was half a day and it changed our actual
recovery position more than any amount of additional backup infrastructure would have. The most
valuable output was not the fixed gaps - it was having a number we could defend.

## Honest scope

One drill, two systems, one afternoon. I have not run a full disaster recovery exercise across an
estate, and I have not been responsible for a real recovery under pressure.
