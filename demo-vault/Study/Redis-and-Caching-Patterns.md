# Redis and caching patterns

Course notes. Concepts, not something I have operated at scale.

## Patterns

- **Cache aside** - the application checks the cache, and on a miss reads the database and populates
  it. The most common pattern. Its weakness is that every miss is a full round trip, so a cold cache
  under load pushes everything at the database at once.
- **Read through / write through** - the cache sits in front and handles population itself. Simpler
  application code, and writes pay the cache latency.
- **Write behind** - writes go to the cache and are flushed to the database asynchronously. Fast, and
  it introduces a window where acknowledged data exists only in the cache.

## Invalidation

- **TTL** is the simplest correct answer and usually the right one. It bounds staleness without
  needing to know when the underlying data changed.
- **Explicit invalidation on write** is precise and gets missed on the code path someone forgot.
- The difficulty is not choosing a strategy; it is that every strategy leaves a window and the
  question is how large a window the use case tolerates.

## Failure modes worth knowing

- **Stampede** - a popular key expires and every concurrent request misses simultaneously, all
  hitting the database. Mitigations: jittered TTLs so keys do not expire together, or a lock so one
  request repopulates while the others wait or serve stale.
- **Penetration** - repeated requests for a key that does not exist reach the database every time.
  Caching the negative result bounds this.
- **Avalanche** - a large set of keys expiring at once, or the cache restarting empty, presenting the
  database with full traffic. Jitter helps the first; warming helps the second.

## Eviction

When memory is full, the eviction policy decides. Approximate LRU is the common default; least
frequently used suits workloads with a stable hot set. The important part is that *something* is
evicted - a cache configured to reject writes when full behaves very differently under pressure from
one that evicts, and the choice should be deliberate.
