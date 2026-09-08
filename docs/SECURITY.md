# Security and Safety Notes

## Design principles

- **Tool-enforced constraints:** hard recipient and food-safety rules are deterministic and are not delegated to free-form model judgment.
- **No unsafe fallback:** insufficient eligible capacity triggers human review; the system never relaxes an allergen or refrigeration rule to complete an allocation.
- **Auditable actions:** state-changing operations append timestamped audit events.
- **Human approval:** risky or unresolved states are explicitly surfaced rather than silently completed.
- **Least data for demo:** the included dataset is synthetic and contains no personal data.

## Production hardening backlog

- replace in-memory storage with DynamoDB and conditional writes;
- use AgentCore Identity/IAM for tool authorization;
- add idempotency keys for notifications and rescue creation;
- encrypt recipient/donor contact data;
- add schema validation for third-party integrations;
- add rate limits and abuse controls;
- use OpenTelemetry/AgentCore observability for immutable operational traces.


## Demo failure injection

The `/api/demo/.../force-logistics-escalation` route intentionally changes synthetic volunteer availability so judges can see the human-escalation behavior on demand. It operates only on in-memory demo data. A production deployment should remove or disable demo-only routes and protect operational mutations with authentication/authorization.
