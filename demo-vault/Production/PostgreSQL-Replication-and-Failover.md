---
tier: production
---

# PostgreSQL streaming replication and failover

We run a primary with two streaming replicas: one synchronous in the same site, one asynchronous off
site. This is what I have actually operated, including two real failovers.

## What I watch

- **Replication lag in bytes, not seconds.** Seconds since the last replayed transaction reads as
  zero on an idle system regardless of health. The byte difference between sent and replayed on
  `pg_stat_replication` is the honest number.
- **Replication slots, carefully.** They guarantee the primary keeps WAL a replica still needs, which
  is exactly what you want - and exactly how you fill the primary's disk when a replica stays down.
  A slot for a decommissioned replica is a time bomb. We alert on WAL directory growth for this
  reason and not for any other.
- **Whether the synchronous replica is actually synchronous.** If it falls out of the configured set,
  commits stop waiting for it and you have silently lost the durability guarantee you designed for.

## Failover

Promotion itself is quick. The parts that go wrong are around it:

- **The old primary must not come back as a primary.** Two writable nodes is the worst outcome
  available, worse than being down, because it is discovered later and reconciled by hand.
- **Applications need to be pointed at the new primary.** Whatever indirection you use - virtual IP,
  connection pooler, DNS - is now the critical path, and its failover time adds to yours.
- **The remaining replica needs rebuilding or rewinding** against the new timeline. Plan for the time
  this takes; until it finishes you have no redundancy.

## Restores are the thing worth practising

Replication is not backup - it replicates the accidental DELETE faithfully and immediately. We keep
base backups plus WAL archiving for point-in-time recovery, and we restore from them on a schedule
rather than assuming they work.

The number that surprised everyone the first time was the restore duration: the base backup restored
quickly, then replaying WAL to the target time took considerably longer than anyone had assumed. That
number is the real RTO, and we only knew it because we ran the drill.
