# 0001 — LocalStack to develop AWS infra for free

**Status:** Accepted
**Date:** 2026-08-05

## Context

The project targets AWS managed databases and services (DynamoDB, CloudWatch), but developing and demonstrating against real AWS costs money and requires an account with credentials that can't live in a public repo. I need the code and the Terraform to exercise the **real AWS APIs** so the skills are genuine, without a bill or a secret.

## Decision

Use **LocalStack** — a container that emulates the AWS APIs locally. Both the Terraform provider and the boto3 / AWS SDK clients point at LocalStack's endpoint (`http://localhost:4566`) by default. A single flag (`use_localstack = false` in Terraform, unset `AWS_ENDPOINT_URL` in the apps) switches everything to real AWS with no code change.

## Consequences

**Positive**
- Anyone can `git clone` and run the whole platform, including "AWS", with just Docker. No account, no cost.
- The code paths are the real ones — same boto3 calls, same Terraform resources, same AWS SDK for Java. It's not mocked.
- Promoting to real AWS is a config change, not a rewrite.

**Negative**
- LocalStack's free tier doesn't emulate *every* AWS feature perfectly (e.g. RDS is limited), which is why the "managed database" here is a real Postgres container standing in for RDS/Aurora, while DynamoDB and CloudWatch run in LocalStack.
- A reviewer sees emulated AWS, not a live account. Mitigated by keeping the switch to real AWS trivial and documenting a free-tier path.

## Alternatives considered

1. **Real AWS free tier.** Works, but requires every reader to have an account and risks accidental charges. Kept as an optional path, not the default.
2. **Mock the AWS SDK.** Rejected — it would prove nothing about actually using AWS.
