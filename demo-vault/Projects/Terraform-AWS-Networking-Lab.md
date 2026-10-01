---
tier: project
---

# Terraform AWS networking lab

A home lab build, not production work - I wanted to understand VPC design by making the mistakes
somewhere harmless.

## What I built

A VPC with public and private subnets across two availability zones, an internet gateway, a NAT
gateway, route tables, security groups, and a small application behind a load balancer. All of it in
Terraform so I could tear it down nightly and stop paying for it.

## What the lab actually taught me

- **Subnets are AZ-scoped and route tables are not.** Getting this backwards is why my first attempt
  had instances in one AZ that could reach the internet and instances in the other that could not.
- **Security groups are stateful; network ACLs are not.** An ACL that allows inbound but forgets the
  ephemeral port range outbound blocks the return traffic, and the symptom is a connection that
  hangs rather than one that is refused.
- **The NAT gateway is the expensive part.** One per AZ is the resilient design and doubles the cost.
  In the lab I ran one and accepted that an AZ failure would take out egress from the other - a
  perfectly reasonable trade for a lab and a bad one for production.
- **State is the whole game with Terraform.** I corrupted local state once by interrupting an apply.
  Moving to remote state with locking was the point where this stopped feeling fragile.

## Habits I kept

- **Always read the plan.** Not skim - read. Every destructive change I nearly made was visible in a
  plan I had not read carefully.
- **Small modules with explicit inputs** beat one large configuration. Not for reuse, which is the
  usual argument, but because the blast radius of an apply is smaller.
- **Tag everything, immediately.** By week two I had resources I could not attribute.

## Honest scope

This is lab work. I have written Terraform to build and destroy an environment I controlled entirely,
on a schedule that suited me, with nothing depending on it. I have not run a Terraform-managed
production estate with multiple engineers applying against shared state, and I would expect the
collaboration and change-control side of that to be most of the real difficulty.
