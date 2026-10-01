---
tier: project
---

# Building out a CI pipeline

An internal project: our deployments were a documented sequence of manual steps, and I moved them to
a pipeline over about six weeks alongside my normal work.

## Where it started

A wiki page with fourteen steps. It worked when followed exactly, which it was not, because steps 6
and 7 were only needed on some releases and everyone remembered that differently. Two of our last
four incidents traced back to a missed step.

## What I built

Stages for lint, unit tests, build, and deploy to staging, with production deploy behind a manual
approval. Artefacts built once and promoted rather than rebuilt per environment - that was the single
change that removed the most class of surprise, because staging and production were now provably the
same build.

## What I learned

- **Start with the boring part.** I wanted to begin with deployment. Beginning with tests running
  automatically on every push built trust with the team, which I needed before anyone would let me
  touch deploys.
- **A flaky test destroys the whole thing.** One test that failed maybe one run in eight taught
  everyone to re-run the pipeline on failure, which is exactly the habit that makes CI worthless. We
  quarantined it the same week.
- **Secrets do not go in the pipeline definition.** Obvious in principle. In practice it took a
  deliberate pass to move the three that had been pasted in during early debugging, and a scan of the
  history afterwards.
- **Deployment needs a rollback path before it needs anything else.** The first version could deploy
  and could not undo. That is a worse position than manual steps, and I should not have shipped it.

## Honest scope

One application, one team, one deployment target. I have not built out pipelines across many services
or dealt with the dependency-ordering problems that come with that. The principles I would carry over
are build-once-promote-many and rollback-before-features; the scale is not something I have operated.
