---
tier: production
---

# Linux service troubleshooting

How I actually work a "the service is down" page on our RHEL 8 fleet. Written up after the
checkout-api incident so the next person on call has the order of operations.

## The order I go in

1. **Is the unit running at all?** `systemctl status <unit>` first, every time. The status output
   already carries the last few journal lines, so it often ends the investigation on its own.
   Active (running) with a recent start time means it crashed and restarted, which is a different
   problem from never having started.
2. **Read the journal for the unit, not the whole system.** `journalctl -u <unit> --since "10 min ago"`.
   Adding `-f` while you reproduce is what catches the ones that only fail under load.
3. **Is it the service or the machine?** Check load, memory and disk before blaming the app.
   A full `/var` looks exactly like an application bug from the logs.
4. **Is it listening where you think?** `ss -ltnp` shows the socket and the owning process. Twice now
   the answer has been that the service bound 127.0.0.1 after a config change and the load balancer
   was hitting the external address.
5. **Can it reach what it depends on?** Database, cache, upstream API. Test from the box itself,
   as the service user, not from your laptop.

## What I learned the hard way

- **`systemctl restart` is a diagnosis, not a fix.** If a restart clears it, you have learned the
  process degrades over time. Note the uptime at failure before you restart, or you have thrown away
  the only evidence.
- **Unit file changes need `daemon-reload`.** Editing the unit and restarting without it gets you the
  old definition and a very confusing twenty minutes.
- **`RestartSec` matters as much as `Restart`.** We had a unit set to restart always with the default
  delay; a bad config change turned into a restart loop that hammered the database. Now the noisy
  services have a backoff and a `StartLimitBurst`.

## The checkout-api incident

Symptom was intermittent 502s from the load balancer, roughly one request in twenty. Status showed
the unit active with an uptime of four minutes. The journal showed a clean start every few minutes
with no error before it. That pattern - clean starts, no crash log - pointed away from the
application, and the OOM killer entries in `dmesg` confirmed it. The service had a memory leak that
only mattered under production traffic volume; the restarts were the kernel reaping it.

Fix in the moment was a memory limit on the unit so it died predictably and quickly instead of
taking the box's cache with it. The real fix was in the application, which took the dev team two
weeks. That gap is the point: the operational mitigation buys the time for the real fix.
