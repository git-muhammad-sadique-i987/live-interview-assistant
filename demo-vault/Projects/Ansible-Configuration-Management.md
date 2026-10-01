---
tier: project
---

# Ansible for configuration management

A proof of concept that became half-adopted, which is its own useful lesson.

## The problem

Thirty-odd Linux hosts configured over four years by several people. Nominally identical, actually
not - different sysctl values, different sudoers, three different NTP configurations. Nobody could
say what the correct state was.

## What I did

Wrote roles for the baseline: users and SSH, time sync, logging, monitoring agent, and the security
settings our policy required. Ran them in check mode against the whole fleet first, which produced
the drift report that made the case better than any argument I made.

## What worked

- **Check mode as a discovery tool.** Before changing anything, running the desired state in check
  mode against the estate tells you exactly how far from it you are.
- **Idempotence is the property that matters.** A playbook you can run repeatedly without fear is one
  people will actually run. Anything with a shell command that is not guarded breaks that property.
- **Inventory groups mirroring the real world.** Environment, role, location. Getting this right made
  the playbooks simple; my first attempt had the environment encoded in variable files and every
  playbook had to know about it.

## What did not work

Adoption. I automated the baseline, and the team kept making one-off changes by hand because that was
faster in the moment. Within three months the drift was returning. The technical work was fine and
the change of habit was the actual project - I did not plan for that at all, and I would approach it
completely differently now: agree first that manual changes are out of bounds, then automate.

## Honest scope

A POC on a fleet I was allowed to experiment with. Roles I wrote and ran myself, not a
production-critical automation estate with change control around it.
