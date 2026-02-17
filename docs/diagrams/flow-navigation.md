# Flow Navigation Map

> Referenced from [`flow-structure.md`](../../flow/flow-structure.md). See that file for full context.

```mermaid
graph LR

  subgraph devLane["Developer Swimlane (CONTRIBUTOR or ADMIN)"]
    p1["P1: Package Browser"]
    p2["P2: Promotion Review"]
    p3["P3: Promotion Status"]
    p4["P4: Deployment Submission"]
    p9["P9: Production Readiness"]
    p10["P10: Extension Manager"]
    p11["P11: Extension Copy Confirmation"]
  end

  subgraph peerLane["Peer Review Swimlane (CONTRIBUTOR or ADMIN)"]
    p5["P5: Peer Review Queue"]
    p6["P6: Peer Review Detail"]
  end

  subgraph adminLane["Admin Swimlane (ADMIN only)"]
    p7["P7: Admin Approval Queue"]
    p8["P8: Mapping Viewer"]
  end

  flowStart(["Start"]) --> p1

  p1 -->|"Review for Promotion"| p2
  p1 -->|"Withdraw"| p1

  p2 -->|"Cancel"| p1
  p2 -->|"Promote"| p3

  p3 -->|"Submit for Peer Review"| p4
  p3 -->|"Test Deploy"| p4
  p3 -->|"Hotfix"| p4
  p3 -->|"Done"| flowEnd(["End"])

  p4 -->|"Submit for Peer Review"| p5
  p4 -->|"Test deployed"| p1

  p9 -->|"Promote to Production"| p4

  p5 -->|"Select review"| p6

  p6 -->|"Approve"| p7
  p6 -->|"Reject"| flowEnd2(["End — branch deleted"])

  p7 -->|"Approve and Deploy"| flowEnd3(["End — deployed"])
  p7 -->|"Deny"| flowEnd4(["End — branch deleted"])
  p7 -.->|"nav"| p8

  p10 -->|"Copy Test to Prod"| p11
  p11 -->|"Cancel"| p10
  p11 -->|"Confirm Copy"| p10
```

## Legend

**Swimlane colors** correspond to authorization tiers:
- Developer Swimlane — accessible to `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN`
- Peer Review Swimlane — accessible to `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` (self-review blocked)
- Admin Swimlane — accessible to `ABC_BOOMI_FLOW_ADMIN` only

**Node shapes:**
- Rounded rectangles (`["..."]`) — dashboard pages (P1–P11)
- Stadium/pill shapes (`(["..."])`) — flow entry/exit points

**Edge labels** — button or trigger name that causes the navigation.

**Dashed arrow** (`-.->`) from P7 to P8 — side navigation (independent page, not part of the main approval flow).

**P9 and P10/P11** are independent entry points accessible from swimlane navigation at any time; they are shown connected to the main flow at the transitions where they hand off.
