# Page 5: Peer Review Queue (Peer Review Swimlane)

## Overview

The Peer Review Queue is the entry point for the peer review layer of the 2-layer approval workflow. Developers and admins authenticate via SSO, see promotions submitted by other users (own submissions are excluded), and select one to review in detail. This is the first approval gate — only after peer approval does a promotion advance to admin review.

## Page Load Behavior

1. **Peer reviewer authentication:**
   - User must authenticate via SSO with `ABC_BOOMI_FLOW_CONTRIBUTOR` OR `ABC_BOOMI_FLOW_ADMIN` group membership
   - If not authorized: Show error "Access denied. This page requires developer or admin privileges."
   - Store reviewer user context: `peerReviewerEmail` (from `$User/Email`), `peerReviewerName` (from `$User/First Name` + `$User/Last Name`)

2. **Message step execution:** `queryPeerReviewQueue`
   - Input:
     - `requesterEmail` = `$User/Email` (used by backend to exclude own submissions)
   - Output: `pendingPeerReviews` array (promotions awaiting peer review, excluding user's own)

3. **Populate peer review queue:**
   - Display pending peer reviews in Data Grid
   - Sort by `initiatedAt` descending (newest first)

4. **Error handling:**
   - If `queryPeerReviewQueue` fails → Navigate to Error Page

## Components

### Peer Review Queue Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `queryPeerReviewQueue` response → `pendingReviews` array
- Flow value: `pendingPeerReviews`

**Columns:**

| Column | Field | Width | Sortable | Formatting |
|--------|-------|-------|----------|------------|
| Submitter | `initiatedBy` | 15% | Yes | Email or name |
| Process Name | `processName` | 17% | Yes | Bold text |
| Components | `componentsTotal` | 8% | Yes | Numeric |
| Created/Updated | `componentsCreated` / `componentsUpdated` | 12% | Yes | "X new, Y updated" |
| Submitted | `initiatedAt` | 15% | Yes | Date/time format |
| Status | `peerReviewStatus` | 10% | Yes | Badge |
| Environment | `targetEnvironment` | 10% | Yes | Badge: "PRODUCTION" blue badge (always — test deployments never reach peer review) |
| Hotfix | `isHotfix` | 8% | Yes | Badge: "EMERGENCY HOTFIX" red badge if true; hidden if false |
| Notes | `notes` | 12% | No | Truncated, tooltip |

**Column Details:**

1. **Submitter**
   - Display: Submitter email or full name
   - Format: Plain text, left-aligned
   - Sortable: Alphabetical

2. **Process Name**
   - Display: Root process name (e.g., "Order Processing Main")
   - Format: Bold text for emphasis
   - Sortable: Alphabetical

3. **Components**
   - Display: Total component count
   - Format: Numeric text, centered
   - Sortable: Numeric order

4. **Created/Updated**
   - Display: "X new, Y updated"
   - Format: Plain text or badge
   - Sortable: By total components

5. **Submitted**
   - Display: Submission timestamp
   - Format: "YYYY-MM-DD HH:mm" or relative time
   - Sortable: Chronological (default descending)

6. **Status**
   - Display: Peer review status
   - Format: Badge — `PENDING_PEER_REVIEW`: Yellow/orange badge
   - Sortable: Alphabetical

7. **Notes**
   - Display: Deployment notes from submitter
   - Format: Truncated to 50 chars with ellipsis, tooltip for full text
   - Empty: "No notes provided" (gray text)

**Row Selection:**
- **Mode:** Single-row selection
- **Visual:** Highlight selected row with accent color
- **On select event:**
  1. Store selected promotion → `selectedPeerReview` Flow value
  2. Navigate to Page 6 (Peer Review Detail)

**Default Sort:**
- `initiatedAt` descending (newest submissions at top)

**Empty State:**
- Message: "No pending peer reviews"
- Submessage: "All promotion submissions have been reviewed or you have no eligible reviews."
- Icon: Checkmark or empty inbox icon

**Pagination:**
- If > 25 requests: Enable pagination (25 rows per page)

---

### Self-Review Prevention

**Implementation:** Dual enforcement

1. **Backend-level (primary):** The `queryPeerReviewQueue` message action excludes promotions where `initiatedBy` matches the `requesterEmail` parameter. The user never sees their own submissions in the queue.

2. **UI-level (fallback):** If a promotion somehow appears where `selectedPeerReview.initiatedBy` equals `$User/Email`:
   - Add a Decision step after row selection
   - Condition: `LOWERCASE($User/Email)` != `LOWERCASE(selectedPeerReview.initiatedBy)`
   - True path: Navigate to Page 6
   - False path: Show inline error banner: "You cannot review your own submission. Please ask another team member to review."

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Peer Review Queue"                                      |
| Reviewer: {peerReviewerName} ({peerReviewerEmail})       |
+----------------------------------------------------------+
| INFO BANNER                                               |
| "Review promotion submissions from your team. Select a   |
|  submission to view details and approve or reject."       |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Peer Review Queue Data Grid                             |
|  +----------------------------------------------------+  |
|  | Submitter | Process | Comps | Created | Submitted |  |
|  |--------------------------------------------------------|
|  | john@co   | Order P | 12    | 2/10    | 2h ago    |  |
|  | jane@co   | API Syn | 5     | 0/5     | 1d ago    |  |
|  | ...       | ...     | ...   | ...     | ...       |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Peer Review Queue"
- Reviewer context: Display name and email
- Subtitle: "2-Layer Approval — Step 1 of 2"

**Info Banner:**
- Light blue or info-colored background
- Brief instructions for the reviewer
- Dismissible (optional)

**Main Area:**
- Peer Review Queue Data Grid
- Full width
- Min height: 300px

### Responsive Behavior

**Desktop (> 1024px):**
- Full table with all columns visible
- Row click navigates to Page 6

**Tablet (768px - 1024px):**
- Scroll table horizontally if needed

**Mobile (< 768px):**
- Card-based layout for queue items
- Tap card to navigate to Page 6

## Accessibility

- **Keyboard navigation:** Tab through grid rows, Enter to select
- **Screen reader:** Announce row details, selection state
- **Focus indicators:** Clear visual focus on selected row
- **ARIA labels:** Proper labels for grid and rows

## User Flow Example

1. **Developer receives email notification**
   - Subject: "Peer Review Needed: Order Processing Main v1.2.3"
   - Clicks link in email

2. **Reviewer authenticates via SSO**
   - `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` group membership validated
   - Redirected to Page 5

3. **Reviewer sees peer review queue**
   - Grid shows pending reviews (own submissions excluded)
   - Newest at top: "Order Processing Main" from john@company.com

4. **Reviewer selects a submission**
   - Row highlights
   - Navigation triggers to Page 6 (Peer Review Detail)
