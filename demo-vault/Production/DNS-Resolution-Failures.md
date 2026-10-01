---
tier: production
---

# DNS resolution failures

The most common "the network is broken" ticket that turns out not to be the network.

## How I isolate it

- **Does the name resolve at all?** `dig <name>` and `dig +short <name>`. If dig works and the
  application does not, it is not DNS - dig bypasses the resolver library's config in ways the
  application does not.
- **Compare `dig` with `getent hosts <name>`.** `getent` goes through nsswitch and the resolver the
  application actually uses. When these two disagree, the answer is in `/etc/nsswitch.conf` or the
  local caching resolver, not in the DNS server.
- **Which server answered?** dig prints the SERVER line. On a box with a local stub resolver you will
  see 127.0.0.53, which tells you nothing about upstream - query the upstream directly with
  `dig @<server> <name>` to compare.
- **Is it just stale?** Check the TTL in the answer. A short remaining TTL on a record that was
  changed recently is a caching problem and will fix itself; a long one will not.

## Things that have actually been the cause

- **Search domain surprises.** A single-label name gets each search domain appended in order. A new
  search domain added to DHCP made an internal short name resolve to something in a different
  environment. Always test with the fully qualified name plus a trailing dot to take search out of
  the picture.
- **One of several resolvers failing.** The resolver tries them in order with a timeout, so a dead
  first entry shows up as *slow* resolution rather than failed resolution. Users report "the site is
  slow", not "DNS is down".
- **Split horizon.** Internal and external views returning different records is by design, and it is
  a genuine problem when a host queries the wrong side after a VPN change.
- **Negative caching.** A record queried before it existed is cached as nonexistent for the SOA
  minimum. People retry, it still fails, and they conclude the record was never created.

## What I tell people

Say "name resolution" rather than "DNS" when you report it. DNS is the service; the failure is
usually in the client's configuration, the search path, or a cache between the two. Naming it
precisely stops three people from checking the DNS servers that were never broken.
