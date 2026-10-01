---
tier: production
---

# NGINX as a reverse proxy, and the TLS parts

We run NGINX in front of about a dozen internal services. Notes from operating it, including the
mistakes that cost us downtime.

## The proxy basics that matter

- **Upstream blocks over inline proxy_pass targets.** Named upstreams give you health checks,
  multiple backends and a single place to change the target during a migration.
- **Pass the original client information through.** Without X-Forwarded-For and X-Forwarded-Proto the
  application sees the proxy as the client, which breaks rate limiting, audit logs and any redirect
  the app builds from the request scheme.
- **Timeouts are three separate settings** - connect, send and read - and the read timeout is the one
  that matters for slow backends. The default is generous enough that a hung backend holds worker
  connections for over a minute.
- **Buffering changes behaviour for streaming responses.** Server-sent events and long downloads need
  it off, or the client sees nothing until the response completes.

## TLS

- **Terminate at the proxy, decide deliberately about the back half.** We terminate at NGINX and go
  plaintext to backends on a trusted network segment. That is a documented decision with a
  compensating control, not an oversight - I have had to defend it in an audit.
- **Certificate chains are the number one cause of "it works in my browser".** Browsers fill in
  missing intermediates from their own cache; curl and most language HTTP clients do not. Test with
  `openssl s_client -connect host:443 -showcerts` and check the chain is complete.
- **Renewal is the actual risk, not configuration.** Ours is automated, and the monitoring alerts at
  21 days remaining. The one outage we had here was a renewal that succeeded while the reload that
  would have picked it up did not.
- **Reload, do not restart.** A reload keeps existing connections; a restart drops them. And test the
  configuration before either - a syntax error in a reload leaves the old config running, which is
  merciful, but a restart with a bad config leaves you with nothing running.

## The header size outage

A partner started sending a much larger authorization header. NGINX rejected the requests with 400
before they ever reached the application, so the application logs were completely clean and we spent
forty minutes looking in the wrong place. The proxy's own error log had the answer immediately.
Lesson kept: when the backend log shows nothing at all, the request never arrived, so read the log of
the thing in front of it.
