# Diagrams Index

Visual diagrams for the Boomi Dev-to-Prod Component Promotion System. All diagrams use [Mermaid](https://mermaid.js.org/) syntax, which GitHub renders natively.

| Diagram | File | Type | Referenced From |
|---------|------|------|----------------|
| Flow Navigation Map | [`flow-navigation.md`](flow-navigation.md) | graph LR | [`flow-structure.md`](../../flow/flow-structure.md) |
| DataHub ER Diagram | [`datahub-er.md`](datahub-er.md) | erDiagram | [`architecture.md`](../architecture.md) |
| Process C Execution Flow | [`process-c-flow.md`](process-c-flow.md) | flowchart TD | [`10-process-c-execute-promotion.md`](../build-guide/10-process-c-execute-promotion.md) |
| Promotion Sequence | [`promotion-sequence.md`](promotion-sequence.md) | sequenceDiagram | [`flow-service-spec.md`](../../integration/flow-service/flow-service-spec.md) |

## Inline Diagrams

The following diagrams are embedded directly in existing files:

| Diagram | Location | Type |
|---------|----------|------|
| System Architecture Overview | [`architecture.md`](../architecture.md) | graph TD |
| Promotion Status Lifecycle | [`architecture.md`](../architecture.md) | stateDiagram-v2 |
| SSO Authorization Model | [`architecture.md`](../architecture.md) | graph TD |
| Branch Lifecycle | [`architecture.md`](../architecture.md) | stateDiagram-v2 |
| Process Build Order | [`00-overview.md`](../build-guide/00-overview.md) | graph LR |
| Build Phase Dependencies | [`00-overview.md`](../build-guide/00-overview.md) | graph LR |
| Process E Family | [`07-process-e-status-and-review.md`](../build-guide/07-process-e-status-and-review.md) | graph TD |
| Dev Swimlane Navigation | [`15-flow-dashboard-developer.md`](../build-guide/15-flow-dashboard-developer.md) | graph LR |
| Deployment Modes Tree | [`11-process-d-package-and-deploy.md`](../build-guide/11-process-d-package-and-deploy.md) | flowchart TD |
