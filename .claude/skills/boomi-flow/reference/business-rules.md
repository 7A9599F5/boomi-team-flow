# Business Rules and Conditional Logic

## Purpose

**Business Rules** define conditional logic that controls flow behavior, routing, and visibility. They enable flows to make decisions based on user input, data values, and application state.

---

## Use Cases

Business Rules are used to:
- **Route flow execution** based on conditions (outcome selection)
- **Control component/page visibility** (show/hide elements)
- **Validate data** and flag errors
- **Create complex decision trees** (branching logic)
- **Enable/disable buttons** based on state

---

## Where Business Rules Are Used

### 1. Outcomes

Determine which outcome path to follow from a step.

**Example: Route based on user selection**

```
Page 2: Promotion Review
  ↓
Button: "Promote"
  ↓
Outcome A: "Submit for Peer Review" (if requiresPeerReview == true)
Outcome B: "Submit Directly" (if requiresPeerReview == false)
```

**Outcome A Business Rule:**

```
ALL (AND)
  requiresPeerReview == $True
```

**Outcome B Business Rule:**

```
ALL (AND)
  requiresPeerReview == $False
```

### 2. Page Conditions

Control when a page is accessible.

**Example: Only show page if user is admin and promotion status is pending**

```
Page Condition:
ALL (AND)
  $User/Groups contains "Boomi Admins"
  promotionStatus == "PENDING_ADMIN_APPROVAL"
```

### 3. Component Visibility

Show/hide components based on conditions.

**Example: Show error message only if failures exist**

```
Presentation: "Error: Some components failed to promote."
Visibility Rule:
ALL (AND)
  promotionResults.componentsFailed > 0
```

**Example: Show admin-only button**

```
Button: "Delete Promotion"
Visibility Rule:
ALL (AND)
  $User/Groups contains "Boomi Admins"
```

**Source:** [Business rules - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Building_and_publishing_flows/Steps/Outcomes/c-flo-Canvas_Business_Rules_e8860ab5-4260-449c-b72d-137d9902baec)

---

## Syntax and Operators

### Comparison Operators

| Operator | Description | Logic |
|----------|-------------|-------|
| `ANY` | OR logic | At least one condition must be true |
| `ALL` | AND logic | All conditions must be true |

### Value Comparisons

| Comparison | Operator | Example |
|------------|----------|---------|
| **Equals** | `==` | `componentsFailed == 0` |
| **Not equals** | `!=` | `reviewStage != "APPROVED"` |
| **Greater than** | `>` | `dependencyTree.length > 20` |
| **Less than** | `<` | `componentsPassed < 50` |
| **Greater than or equal** | `>=` | `promotionResults.componentsPassed >= 50` |
| **Less than or equal** | `<=` | `promotionResults.componentsFailed <= 0` |
| **Contains** | `contains` | `$User/Groups contains "Boomi Admins"` |
| **Is empty** | `is empty` | `deploymentRequest.notes is empty` |
| **Is not empty** | `is not empty` | `selectedPackage is not empty` |

### Nesting

Business rules can be **nested** to create complex conditions.

**Example: Nested ANY within ALL**

```
ALL (AND)
  - CompanyCar == $False
  - OfficeLocation == "Chesterbrook"
  - ANY (OR)
      - WorkPhone == "Apple"
      - WorkPhone == "Samsung"
```

**Logic:**

```
IF (Company Car is False)
  AND (Office Location is Chesterbrook)
  AND (Work Phone is Apple OR Work Phone is Samsung)
THEN
  Condition is met
```

---

## Simple Business Rule Examples

### Example 1: Outcome Routing (Simple Condition)

**Scenario:** Route flow based on whether user requires a company credit card.

**Setup:**

```
Page: Onboarding Form
  ↓
Toggle: "Do you need a company credit card?"
  - Value binding: requiresCreditCard (boolean)
  ↓
Button: "Continue"
  ↓
Outcome A: "Initiate Credit Card Request"
  Business Rule:
  ALL (AND)
    requiresCreditCard == $True
  → Next page: Credit Card Form

Outcome B: "Skip Credit Card"
  Business Rule:
  ALL (AND)
    requiresCreditCard == $False
  → Next page: Continue Onboarding
```

**Logic:**
- If user selected "Yes" (`requiresCreditCard == $True`), follow Outcome A
- If user selected "No" (`requiresCreditCard == $False`), follow Outcome B

### Example 2: Button Enablement

**Scenario:** Enable "Submit for Deployment" button only if no components failed.

**Setup:**

```
Button: "Submit for Deployment"
Enabled when:
ALL (AND)
  promotionResults.componentsFailed == 0
```

**Logic:**
- If `componentsFailed == 0`, button is enabled
- If `componentsFailed > 0`, button is disabled (grayed out)

### Example 3: Component Visibility

**Scenario:** Show error message only if components failed.

**Setup:**

```
Presentation: "Error: Some components failed to promote."
Visibility Rule:
ALL (AND)
  promotionResults.componentsFailed > 0
```

**Logic:**
- If `componentsFailed > 0`, show error message
- If `componentsFailed == 0`, hide error message

### Example 4: Page Condition (Access Control)

**Scenario:** Only allow admins to access deployment page.

**Setup:**

```
Page: Deployment Configuration
Page Condition:
ALL (AND)
  $User/Groups contains "Boomi Admins"
```

**Logic:**
- If user is in "Boomi Admins" group, page is accessible
- If user is NOT in "Boomi Admins" group, page is hidden (redirect to error page)

---

## Complex Business Rule Examples

### Example 5: Nested Conditions (Multiple Criteria)

**Scenario:** Show component only if user meets all conditions:
- Company car NOT required
- Office location is "Chesterbrook"
- Work phone is "Apple" OR "Samsung"

**Business Rule:**

```
ALL (AND)
  - CompanyCar == $False
  - OfficeLocation == "Chesterbrook"
  - ANY (OR)
      - WorkPhone == "Apple"
      - WorkPhone == "Samsung"
```

**Logic:**

```
IF (CompanyCar == $False)
  AND (OfficeLocation == "Chesterbrook")
  AND (WorkPhone == "Apple" OR WorkPhone == "Samsung")
THEN
  Show component
ELSE
  Hide component
```

### Example 6: Multi-Path Routing with Priority

**Scenario:** Route promotion based on number of components and user role.

**Setup:**

```
Page 2: Promotion Review
  ↓
Button: "Promote"
  ↓
Outcome A: "Skip Peer Review" (admin bypass)
  Business Rule:
  ALL (AND)
    $User/Groups contains "Boomi Admins"
    dependencyTree.length < 10
  Order: 0 (highest priority)
  → Direct to Admin Approval

Outcome B: "Require Peer Review" (standard workflow)
  Business Rule:
  ALL (AND)
    dependencyTree.length >= 10
  Order: 1
  → Peer Review Swimlane

Outcome C: "Skip Peer Review" (small promotions)
  Business Rule:
  ALL (AND)
    dependencyTree.length < 10
  Order: 2 (lowest priority)
  → Direct to Admin Approval
```

**Logic:**
- If user is admin AND < 10 components → Outcome A (bypass peer review)
- If >= 10 components → Outcome B (require peer review)
- If < 10 components (and not admin) → Outcome C (skip peer review)

**Priority:**
- Outcome A (order 0) takes precedence over Outcome B (order 1)
- If multiple outcomes match, lowest order number wins

### Example 7: Self-Review Prevention

**Scenario:** Prevent developers from reviewing their own promotions.

**Setup:**

```
Page 5: Peer Review Queue (on page load)
  ↓
Message Step: queryPeerReviewQueue
  Request:
  {
    "reviewStage": "PENDING_PEER_REVIEW",
    "excludeSubmittedBy": $User/Email
  }
  → Backend filters out records where initiatedBy == current user

Page 6: Peer Review Detail (on page load)
  ↓
Decision Step: Check Self-Review
  ↓
Outcome A: "Allow Access"
  Business Rule:
  ALL (AND)
    selectedPeerReview.initiatedBy != $User/Email
  → Page 6 (continue)

Outcome B: "Block Access"
  Business Rule:
  ALL (AND)
    selectedPeerReview.initiatedBy == $User/Email
  → Error Page ("You cannot review your own submission")
```

**Logic:**
- If `selectedPeerReview.initiatedBy != $User/Email`, allow access to Page 6
- If `selectedPeerReview.initiatedBy == $User/Email`, redirect to Error Page

---

## Outcome Priority

If multiple outcomes have business rules that match, Flow follows the outcome with the **highest priority (lowest order number)**.

### Order Values

| Order | Priority | Description |
|-------|----------|-------------|
| **0** | Highest | Evaluated first, takes precedence |
| **1** | Medium | Evaluated if order 0 doesn't match |
| **2** | Low | Evaluated if order 0 and 1 don't match |
| **...** | Lower | Continue in ascending order |

### Example: Fallback Logic

**Scenario:** Route to different pages based on promotion status, with fallback.

**Setup:**

```
Decision Step: Route by Status
  ↓
Outcome A: "Success"
  Business Rule:
  ALL (AND)
    promotionResults.success == $True
    promotionResults.componentsFailed == 0
  Order: 0
  → Page 3: Promotion Status

Outcome B: "Partial Success"
  Business Rule:
  ALL (AND)
    promotionResults.success == $True
    promotionResults.componentsFailed > 0
  Order: 1
  → Page 3: Promotion Status (with warnings)

Outcome C: "Failure"
  Business Rule:
  ALL (AND)
    promotionResults.success == $False
  Order: 2
  → Error Page

Outcome D: "Unknown" (fallback)
  Business Rule: (none, always matches)
  Order: 3
  → Error Page (unexpected state)
```

**Logic:**
- If success AND no failures → Outcome A (order 0)
- If success AND some failures → Outcome B (order 1)
- If failure → Outcome C (order 2)
- If none match → Outcome D (order 3, fallback)

**Best practice:** Always provide a fallback outcome (no business rule, lowest order) to handle unexpected states.

---

## Decision Steps vs Business Rules on Outcomes

### Decision Step

**Purpose:** Dedicated step for routing logic without UI component.

**How it works:**
- Evaluates Flow Values and routes to next step
- No user interaction
- Useful for complex branching without user input

**Example: Error Handling After Message Step**

```
Message Step: executePromotion
  ↓
Decision Step: Check Success
  ↓                    ↓
Outcome A            Outcome B
(success == true)    (success == false)
  ↓                    ↓
Page 3: Results      Error Page
```

**Decision Step Business Rules:**
- **Outcome A**: `promotionResults.success == $True`
- **Outcome B**: `promotionResults.success == $False`

### Business Rules on Outcomes

**Purpose:** Attached to outcomes from pages, messages, etc.

**How it works:**
- Triggered by user actions (button clicks)
- Conditional routing based on user selections
- More common pattern for user-driven workflows

**Example: Approval Workflow**

```
Page 6: Peer Review Detail
  ↓
Button: "Approve"
  ↓
Outcome: "Approve"
  Business Rule:
  ALL (AND)
    reviewNotes is not empty
  → Message Step: submitPeerReview (action: "APPROVED")

Button: "Reject"
  ↓
Outcome: "Reject"
  Business Rule:
  ALL (AND)
    reviewNotes is not empty
  → Message Step: submitPeerReview (action: "REJECTED")
```

### When to Use Each

| Scenario | Use Decision Step | Use Business Rules on Outcomes |
|----------|-------------------|--------------------------------|
| **User-driven navigation** | No | Yes |
| **Conditional routing after API call** | Yes | No |
| **Complex branching without user input** | Yes | No |
| **Approval workflows** | No | Yes |
| **Error handling** | Yes | No |
| **Form validation** | No | Yes (enable/disable buttons) |

---

## Best Practices

### 1. Keep Rules Simple

**Guideline:** Complex rules are hard to debug and maintain.

**Bad practice:**

```
ALL (AND)
  - ANY (OR)
      - ALL (AND)
          - fieldA == "X"
          - fieldB == "Y"
      - ALL (AND)
          - fieldC == "Z"
          - fieldD == "W"
  - ANY (OR)
      - fieldE > 10
      - fieldF < 5
```

**Good practice:**

```
Decision Step: Complex Routing
  ↓
Outcome A:
  ALL (AND)
    fieldA == "X"
    fieldB == "Y"
    fieldE > 10

Outcome B:
  ALL (AND)
    fieldC == "Z"
    fieldD == "W"
    fieldF < 5
```

**Benefit:** Easier to understand, test, and debug.

### 2. Use Decision Steps for Complex Logic

**Guideline:** Better than nested business rules on outcomes.

**When to use Decision Step:**
- More than 2-3 conditions
- Nested ANY/ALL logic
- Error handling after message steps

### 3. Test All Paths

**Guideline:** Ensure every outcome path is reachable and tested.

**Test cases:**
- Happy path (all conditions met)
- Edge cases (null values, empty lists, extreme numbers)
- Error conditions (API failures, validation errors)

### 4. Document Rule Intent

**Guideline:** Add comments in page metadata explaining why rule exists.

**Example:**

```
Page 6: Peer Review Detail
Metadata:
  - Comment: "Self-review prevention: Redirect to error page if user tries to review their own submission"

Decision Step: Check Self-Review
Outcome A: "Allow Access"
  Business Rule: selectedPeerReview.initiatedBy != $User/Email
Outcome B: "Block Access"
  Business Rule: selectedPeerReview.initiatedBy == $User/Email
```

### 5. Outcome Priority

**Guideline:** Use order numbers intentionally for fallback logic.

**Pattern:**

```
Outcome A: Most specific condition (order 0)
Outcome B: Less specific condition (order 1)
Outcome C: Fallback (no rule, order 2)
```

**Benefit:** Clear precedence, prevents ambiguous routing.

### 6. Avoid Hardcoded Values

**Guideline:** Use Flow Values instead of hardcoded strings/numbers.

**Bad practice:**

```
Business Rule:
ALL (AND)
  componentType == "Process"
```

**Good practice:**

```
Flow Value: expectedComponentType = "Process"

Business Rule:
ALL (AND)
  componentType == expectedComponentType
```

**Benefit:** Easier to change, less error-prone.

---

## Validation Patterns

### Pattern 1: Required Fields

**Use case:** Enable button only if all required fields are filled.

**Setup:**

```
Button: "Submit"
Enabled when:
ALL (AND)
  deploymentRequest.notes is not empty
  selectedPackage is not empty
  dependencyTree.length > 0
```

### Pattern 2: Format Validation

**Use case:** Enable button only if email format is valid.

**Setup:**

```
Flow Value: emailValid (boolean, set via business rule or custom component)

Button: "Send Notification"
Enabled when:
ALL (AND)
  emailAddress is not empty
  emailValid == $True
```

### Pattern 3: Range Validation

**Use case:** Show warning if number is out of expected range.

**Setup:**

```
Presentation: "Warning: Unusual number of dependencies (expected 1-20)"
Visibility Rule:
ANY (OR)
  dependencyTree.length < 1
  dependencyTree.length > 20
```

---

## Troubleshooting

### Issue: Business rule always true/false

**Possible causes:**
1. Typo in Flow Value name (case-sensitive)
2. Flow Value is null/undefined
3. Data type mismatch (string vs. number)
4. Operator precedence issue

**Resolution:**
1. Double-check Flow Value name (exact match)
2. Use debug mode to inspect Flow Value values
3. Ensure data types match (use `.toString()` or `.toInteger()` in message step)
4. Simplify rule, test each condition individually

### Issue: Multiple outcomes matching

**Possible causes:**
1. Business rules not mutually exclusive
2. Order priority not configured correctly

**Resolution:**
1. Review business rules, ensure only one should match
2. Use order numbers to define precedence
3. Add fallback outcome (no rule, lowest order)

### Issue: Outcome not following expected path

**Possible causes:**
1. Business rule evaluating incorrectly
2. Flow Value value unexpected
3. Operator precedence issue

**Resolution:**
1. Use debug mode to inspect Flow Values at decision point
2. Add logging (message step that logs state)
3. Simplify rule, test each condition individually

---

## Sources

- [Business rules - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Building_and_publishing_flows/Steps/Outcomes/c-flo-Canvas_Business_Rules_e8860ab5-4260-449c-b72d-137d9902baec)
- [Get Started with Decision Map & Business Rules in Flow](https://community.boomi.com/s/article/Get-Started-with-Decision-Map-Business-Rules-in-Flow)
