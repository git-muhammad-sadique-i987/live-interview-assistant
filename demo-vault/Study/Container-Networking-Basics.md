# Container networking basics

Course notes.

## Namespaces

A container gets its own network namespace: its own interfaces, routing table, and firewall rules. A
virtual ethernet pair connects it to the host, one end inside the namespace and one on a host bridge.
That is the whole mechanism - the isolation is a kernel feature, not something the container runtime
invents.

## The common driver models

- **Bridge** - the default. Containers on the same bridge reach each other directly; outbound traffic
  is NATed behind the host address. Inbound requires explicit port publishing.
- **Host** - no separate namespace. No NAT overhead and no isolation, and port conflicts with the host
  become real.
- **None** - no connectivity, for workloads that should have none.
- **Overlay** - encapsulates traffic so containers on different hosts share a network. The
  encapsulation costs some MTU, which is the source of a classic failure where small packets work and
  large ones vanish.

## Names

The runtime provides DNS for container names on a user-defined network. Relying on IP addresses is
fragile because addresses are reassigned on restart. On the default bridge this resolution is not
available, which is why a user-defined network is generally recommended.

## Publishing ports

Publishing maps a host port to a container port through NAT rules. Two consequences that surprise
people: the container sees the gateway address as the source rather than the real client unless
something preserves it, and publishing on all interfaces exposes the service beyond the host, which
is not always what was intended.

## Where I would expect trouble

MTU mismatches on overlay networks, NAT hiding client addresses from application logs, and firewall
rules on the host interacting with rules the runtime manages. All three are things I have read about
rather than debugged.
