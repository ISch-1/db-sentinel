# 0005 — Terraform for all cloud resources

**Status:** Accepted
**Date:** 2026-08-05

## Context

The platform needs cloud resources: DynamoDB tables for state, CloudWatch alarms for paging. These could be created by clicking in the AWS console — but that's unrepeatable, undocumented, and impossible to review.

## Decision

**All** cloud resources are defined in **Terraform** (`infra/terraform/`). Nothing is created by hand. Applications read resources but never create them — that boundary belongs to Terraform. The same configuration targets LocalStack (dev) or real AWS (prod) via one variable.

## Consequences

**Positive**
- Infrastructure is versioned, reviewable in a pull request, and reproducible — `terraform apply` builds the same thing every time.
- The DynamoDB tables and CloudWatch alarms are self-documenting: the `.tf` files *are* the spec.
- Tearing everything down is one command (`terraform destroy`) — no orphaned resources quietly costing money.

**Negative**
- Terraform state has to be managed; for a single-dev demo local state is fine, but a team needs a remote backend (S3 + DynamoDB lock). Noted for production.
- There's a learning curve, but it's exactly the IaC skill the role asks for (Terraform / CloudFormation).

## Alternatives considered

1. **AWS Console (ClickOps).** Unrepeatable and unreviewable. Rejected.
2. **CloudFormation.** Equivalent and AWS-native; the role lists both. Chose Terraform for its multi-cloud ubiquity and cleaner LocalStack story.
3. **CDK / Pulumi (infra in a general language).** Powerful, but Terraform's declarative model is the industry default for this kind of resource management.
