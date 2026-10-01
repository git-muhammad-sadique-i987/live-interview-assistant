# Kafka fundamentals

Course notes, not operational experience.

## The model

A topic is split into partitions; a partition is an append-only ordered log. Order is guaranteed
within a partition and not across a topic - which is the single most important consequence of the
design, because it means the partition key determines what can be ordered.

Consumers read at their own offset. Because the log persists independently of consumption, a consumer
can replay from an earlier offset, and multiple independent consumers can read the same data without
affecting each other.

## Consumer groups

Each partition is assigned to exactly one consumer within a group. Consequences:

- Parallelism within a group is capped by partition count. More consumers than partitions leaves some
  idle.
- Adding or removing a consumer triggers a rebalance, during which processing pauses.
- Different groups are independent - each maintains its own offsets over the same partitions.

## Delivery guarantees

- **At most once** - commit the offset before processing. Loses messages on a crash.
- **At least once** - process, then commit. Duplicates on a crash, which is why consumers are
  normally written to be idempotent.
- **Exactly once** - available within Kafka using transactions and idempotent producers, but the
  guarantee covers the Kafka-to-Kafka path. Any external side effect is still yours to make
  idempotent.

## Durability

Replication factor sets how many brokers hold a partition. `min.insync.replicas` sets how many must
acknowledge a write for it to be accepted with acks=all. The two together, not either alone,
determine what you survive: replication factor 3 with min.insync.replicas 2 tolerates one broker
loss without losing writes and stops accepting them if a second goes.

## Retention

Time based, size based, or compacted. Log compaction keeps the most recent value per key
indefinitely, which makes a topic usable as a changelog you can rebuild state from.
