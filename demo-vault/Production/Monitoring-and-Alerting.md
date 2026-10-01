---
tier: production
---

# Monitoring and alerting in practice

We run Prometheus for metrics with Alertmanager for routing, and a separate log pipeline. These are
the operational lessons, not the setup instructions.

## Alerts

- **Alert on symptoms, not causes.** "Error rate above 2% for five minutes" is actionable at 3am.
  "CPU above 80%" is not - it is sometimes fine and sometimes fatal, so it trains people to ignore it.
- **Every alert needs an owner and a runbook link.** An alert nobody knows how to action is a
  notification, and notifications get muted.
- **The `for` duration is what separates a page from noise.** Most transient spikes resolve inside a
  minute. Requiring the condition to hold removes the majority of false pages at the cost of a small
  delay in the real ones, and that trade is worth it every time.
- **Review what fired.** We look at the past month's pages in a monthly half hour: anything that
  fired and needed no action gets tuned or deleted. Alert volume goes up on its own otherwise.

## Dashboards

The useful dashboard answers "is it healthy" in about five seconds. Traffic, error rate, latency,
saturation - on one screen, and then links to the detailed views. A dashboard with forty panels is
where you go after you already know what is wrong.

## What I got wrong early

I instrumented what was easy to measure rather than what mattered. Plenty of host-level metrics, no
end-to-end request latency, so a degradation in a dependency looked completely healthy on every
dashboard we had while users were plainly suffering. Adding a small number of service-level metrics
that reflect user experience did more for us than every host metric combined.

The second mistake was alert thresholds set from intuition. Thresholds set from a week of observed
data are defensible and roughly correct; thresholds set from a guess are argued about for months.
