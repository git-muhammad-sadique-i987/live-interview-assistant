# Kubernetes scheduling and resources

Course notes. I have not run Kubernetes in production.

## Requests and limits

- **Requests** are what the scheduler uses to place a pod. A node is considered to have room based on
  the sum of requests, not on actual usage, so a cluster can look full while the nodes are idle.
- **Limits** are enforced at runtime. Exceeding a CPU limit throttles the container; exceeding a
  memory limit gets it killed, because memory cannot be reclaimed from a process the way CPU time
  can.
- Setting requests far below actual usage overcommits the node and produces eviction under pressure.
  Setting them equal to limits gives predictability at the cost of density.

## Quality of service classes

- **Guaranteed** - requests equal limits for every container. Evicted last.
- **Burstable** - requests set, limits higher or absent. Evicted after BestEffort.
- **BestEffort** - nothing set. First to be evicted under node pressure.

The class is derived from what you set, not declared, which is why pods get evicted in an order
nobody chose deliberately.

## How placement is decided

Filtering removes nodes that cannot run the pod at all - insufficient resources, taints not
tolerated, node selectors unmatched. Scoring ranks what remains. Influences on the outcome:

- **nodeSelector and node affinity** - hard or soft constraints on which nodes are acceptable.
- **Taints and tolerations** - the node's side of the same negotiation: a taint repels pods that do
  not tolerate it, which is how you reserve nodes for particular workloads.
- **Pod affinity and anti-affinity** - place near or away from other pods. Anti-affinity across a
  failure domain is how you avoid every replica landing in one zone.
- **Topology spread constraints** - a more direct expression of the same goal, with a tolerance for
  how uneven the spread may become.

## Why pods stay Pending

Insufficient resources on every node, no node tolerating the taints, an unbound persistent volume
claim, or affinity rules that cannot be satisfied together. The scheduler records the reason in the
pod's events, which is the first thing to read.
