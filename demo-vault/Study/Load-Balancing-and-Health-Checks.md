# Load balancing and health checks

Course notes.

## Algorithms

- **Round robin** - even distribution, ignores that requests differ in cost.
- **Least connections** - sends to the backend with the fewest active connections. Better when
  request durations vary widely.
- **Weighted** variants of either, for backends of unequal capacity, and for gradual rollouts.
- **Hashing on a key** - the same client or the same key lands on the same backend. Gives you
  stickiness without server-side session state; a backend leaving reshuffles more than you might
  expect unless the hash is consistent.
- **Consistent hashing** - reshuffles only the keys belonging to the departed node rather than
  remapping everything, which is what makes it usable for caches.

## Layer 4 versus layer 7

L4 forwards on address and port, cheaply and without seeing the request. L7 parses the request and
can route on path, header or method, terminate TLS, retry idempotent requests and rewrite. The cost
is CPU and a component that now understands your protocol.

## Health checks, where the subtlety is

- **Passive** checks observe real traffic and mark a backend down after failures. No extra load, and
  it only notices after real requests have already failed.
- **Active** checks probe on an interval. They detect a dead backend before users do, and they only
  test what the probe tests.
- A health check hitting a static endpoint reports healthy for a process whose database connection
  pool is exhausted. A check that exercises dependencies reports unhealthy for a shared dependency
  outage and removes every backend at once, which turns a degradation into an outage.

The usual resolution is two checks: a shallow one deciding whether to route traffic, and a deeper one
for alerting and human attention.

## Draining

Removing a backend abruptly kills in-flight requests. Draining stops new connections while allowing
existing ones to complete within a timeout, which is what makes a rolling deploy invisible to users.
