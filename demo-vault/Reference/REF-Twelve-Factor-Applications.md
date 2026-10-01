# Reference: the twelve-factor application

Framework reference. A widely cited set of practices for applications intended to be deployed to
cloud platforms, summarised.

1. **Codebase** - one codebase tracked in version control, many deploys.
2. **Dependencies** - declared and isolated explicitly; never rely on what happens to be on the host.
3. **Config** - stored in the environment, not in the code. The test is whether the codebase could be
   open sourced without leaking credentials.
4. **Backing services** - databases, queues, caches treated as attached resources, swappable by
   changing configuration.
5. **Build, release, run** - strictly separate stages. A release is an immutable build plus config;
   you cannot change code at runtime.
6. **Processes** - stateless and share nothing. Persistent state belongs in a backing service.
7. **Port binding** - the application exports its service by binding a port, rather than requiring
   injection into a server at runtime.
8. **Concurrency** - scale out by running more processes rather than making one process larger.
9. **Disposability** - fast startup and graceful shutdown, so instances can be created and destroyed
   freely.
10. **Dev/prod parity** - keep environments as similar as possible in time, personnel and tooling.
11. **Logs** - treat as event streams written to stdout; the environment handles routing and storage.
12. **Admin processes** - one-off tasks run as processes in an identical environment against the same
    codebase.

## What to note about it

The factors are not commandments and several are contested in specific contexts - strict statelessness
in particular is a cost some workloads should not pay. Their value is as a checklist of the places
where an application couples itself to a specific machine, since those are the couplings that make it
hard to deploy, scale or recover.
