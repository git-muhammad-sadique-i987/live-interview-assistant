# Consistency models, CAP and PACELC

Course notes.

## CAP, stated carefully

During a network partition, a distributed system must choose between remaining available and
remaining consistent. It is a statement about behaviour *during a partition*, not a permanent
three-way choice, and the common shorthand of calling a database "AP" or "CP" describes what it does
when partitioned rather than what it is.

## PACELC, which is the more useful version

If Partitioned, choose Availability or Consistency; Else, choose Latency or Consistency. This extends
the idea to normal operation, which is where systems spend nearly all their time. A system that
chooses consistency in both cases pays latency on every request; one that relaxes consistency when
healthy is faster and returns stale reads.

## The consistency models in the middle

- **Strong / linearizable** - every read sees the most recent write. Requires coordination, so it
  costs latency and availability.
- **Sequential** - all nodes see operations in the same order, not necessarily real time order.
- **Causal** - operations that are causally related are seen in order by everyone; unrelated ones may
  be seen differently. Enough for many applications and far cheaper than strong.
- **Read your writes** - a client always sees its own writes. Often what users actually mean by
  "consistent", and achievable by routing a session's reads to the node that took its write.
- **Eventual** - replicas converge given no new writes. Says nothing about when.

## Where the choice shows up

The interesting question is rarely which model the database offers globally, but which one a
particular operation needs. Posting a comment and then not seeing it is a bug users report
immediately; a follower count that is briefly stale is not. Different guarantees for different
operations against the same store is usually the practical answer.
