# MindBloom — Task 08 Completion Report: Parent Dashboard, Child Profiles & Assessment History

**Project:** MindBloom — Child Aptitude & Interest Assessment System  
**University Course:** B.Tech CSE Semester Project  
**Framework:** Django 5.2.19 (Python 3.11.9)  
**Database:** SQLite (`db.sqlite3`)  
**Completed:** November 2026  

---

## 1. Executive Summary & Existing Architecture Inspected

Task 08 introduces the **Parent & Educator Dashboard** — the central workspace for authenticated users managing child learners. Prior to this task, parents had no centralized screen to view all their children, inspect historical assessment attempts across tracks, compare progress over time, or manage profile details safely.

### Inspected Relationships & Data Model
The implementation reuses MindBloom's existing relational hierarchy without introducing redundant models or altering ownership semantics:

```text
User (Parent/Educator)
  │
  └── (1:N via Child.owner) ──► Child
                                  │
                                  ├── (1:N via Assessment.child) ──► Assessment
                                  │                                    │
                                  │                                    ├── (1:N) ──► Answer
                                  │                                    │
                                  │                                    └── (1:1) ──► Result
```

- **Strict Ownership:** Every child record is associated directly with `request.user` via `Child.owner`.
- **Zero Redundant Schemas:** No separate "Parent" or "Statistic" models were introduced; all metrics and comparisons are calculated deterministically via Django ORM queries and service helpers.
- **Session Continuity:** Sessions are synchronized with `active_child_id` upon accessing or continuing assessments to prevent cross-profile collisions.

---

## 2. Parent Dashboard Implementation (`/dashboard/`)

URL: `/dashboard/` (`core:dashboard`)  
View: `dashboard` in [`core/views.py`](file:///e:/project/aptitude_finder/core/views.py)  
Template: [`core/templates/core/dashboard.html`](file:///e:/project/aptitude_finder/core/templates/core/dashboard.html)

### Key Sections:
1. **Welcome Section:**
   - Displays authenticated parent's actual first name or username (e.g., *"Welcome back, Priya!"*).
   - Dynamic localized date display (`current_date|date:"l, F d, Y"`).
   - Primary action buttons: `Add Child` (`core:child_add`) and `Start Assessment` (`assessment:register`).
2. **Dashboard Statistics Cards:**
   - **Total Children:** Count of `Child` profiles owned by `request.user`.
   - **Total Assessments:** Total attempts initiated across all owned children.
   - **Completed Assessments:** Filtered strictly to `status=COMPLETED`.
   - **Pending Assessments:** Filtered strictly to `status=PENDING`.
3. **My Children Grid:**
   - Visual cards for all owned child profiles.
   - Initial avatar badge, age, gender, school grade, developmental age group badge (e.g., `Early Exploration (Ages 5–8)`).
   - Real-time counts: Total, Completed, and Pending modules per child.
   - Latest activity timestamp.
   - Action triggers: `View Profile` (`core:child_detail`) and `Start Assessment` (`assessment:selection`).
4. **Empty State:**
   - When no child profiles exist for the parent, an encouraging empty-state banner renders with an `Add Your First Child` call-to-action.

---

## 3. Statistics Calculation Logic

All counts are strictly scoped to `request.user`'s children to guarantee privacy and isolation:

```python
user_children = Child.objects.filter(owner=request.user).order_by('-created_at')
total_children = user_children.count()

user_assessments = Assessment.objects.filter(child__owner=request.user)
total_assessments = user_assessments.count()
completed_assessments_count = user_assessments.filter(status=Assessment.AssessmentStatus.COMPLETED).count()
pending_assessments_count = user_assessments.filter(status=Assessment.AssessmentStatus.PENDING).count()
```

To avoid $N+1$ query overhead when rendering cards, `prefetch_related('assessments__result')` is utilized.

---

## 4. Child Profile & Individual Assessment History (`/dashboard/child/<child_id>/`)

URL: `/dashboard/child/<child_id>/` (`core:child_detail`)  
View: `child_detail` in [`core/views.py`](file:///e:/project/aptitude_finder/core/views.py)  
Template: [`core/templates/core/child_detail.html`](file:///e:/project/aptitude_finder/core/templates/core/child_detail.html)

### Page Structure:
1. **Child Information Card:**
   - Name, Age, Gender, Grade, Developmental Stage label, Profile creation date.
   - Profile management action buttons: `Edit Profile`, `Delete Profile` (danger zone), and `Start Assessment`.
2. **Track Summaries (Aptitude vs. Interest):**
   - **Aptitude Evaluation Card:** Total attempts, completed count, pending count, latest assessment date, latest percentage score (e.g., `80.0%`).
   - **Interest Discovery Card:** Total attempts, completed count, pending count, latest assessment date, latest top interest domains (e.g., `Science and Technology, Arts and Creativity`). Never displays an aptitude percentage for interest evaluations.
3. **Chronological Assessment History Table:**
   - Displays all child attempts ordered newest first (`-created_at`, `-id`).
   - Columns:
     - **Assessment Track:** Type badge (`Aptitude Assessment` or `Interest Assessment`).
     - **Date:** Formatted timestamp.
     - **Status:** Status badge (`Completed` in teal or `Pending` in amber).
     - **Result:** Percentage for completed aptitude assessments, top domains for completed interest assessments, or `—` for pending.
     - **Action:** `View Report` (links to `results:assessment_report`) for completed, or `Continue` (links to `assessment:take`) for pending.
   - When no assessments exist, renders a clean empty state with a start assessment link.

---

## 5. Child Profile Management (Add, Edit, Safe Delete)

### A. Add Child (`/dashboard/child/add/`)
- URL: `core:child_add`
- Form: Reuses `ChildRegistrationForm` with age validation ($5 \le \text{age} \le 18$) and trimmed name requirements.
- Automatically sets `child.owner = request.user` and synchronizes the session active child.

### B. Edit Child (`/dashboard/child/<child_id>/edit/`)
- URL: `core:child_edit`
- Form: `ChildRegistrationForm(instance=child)`.
- Updates `name`, `age`, `gender`, and `grade`.
- **Developmental Calibration:** When the child's age is changed, `child.age_group` dynamically recalibrates for all upcoming assessments.
- **Historical Data Preservation:** Changing a child's age never mutates historical completed assessment records or rewrites generated result records.

### C. Safe Delete Child (`/dashboard/child/<child_id>/delete/`)
- URL: `core:child_delete`
- **GET Request (Confirmation Step):** Renders a dedicated safety screen ([`core/templates/core/child_confirm_delete.html`](file:///e:/project/aptitude_finder/core/templates/core/child_confirm_delete.html)) detailing the exact cascading impacts:
  - 1 Child Profile.
  - Total assessment attempts that will be removed (breakdown by Aptitude and Interest).
  - Number of generated strength reports and recorded question answers.
  - Explicit warning that the deletion is permanent and cannot be undone.
- **POST Request:** Deletes the record, clears active session state if matching, and redirects to the dashboard with an informative message.

---

## 6. Longitudinal Attempt Comparison

Implemented per Section 7 of the specification for children who have completed multiple attempts within the same module:

### Aptitude Progression Analysis:
- Compares the two most recent completed attempts chronologically (`previous` vs `latest`).
- Calculates overall score change with signed difference (`+X.X%` or `-X.X%`).
- Category-level breakdown across all 5 cognitive domains (`Logical Reasoning`, `Numerical Ability`, `Spatial Reasoning`, `Pattern Recognition`, `Problem Solving`) with previous percentage, latest percentage, and net change.
- Educational Growth Disclaimer: Explains that score variations reflect developmental curiosity, question sampling, and practice engagement rather than fixed intellectual capability.

### Interest Preference Shifts:
- Compares previous distribution percentages vs latest distribution percentages across all 5 thematic domains (`Science and Technology`, `Arts and Creativity`, `Social Activities`, `Nature and Exploration`, `Sports and Physical Activities`).
- Displays preference shifts (`+X.X%` or `-X.X%`).
- Curiosity Evolution Disclaimer: Explains that preference shifts reflect natural developmental broadening and new experiential exposure.

### Single-Attempt & Type Separation Rules:
- If only one attempt of a track is completed, displays an informative prompt explaining that completing a second attempt in the future will unlock longitudinal comparative insights.
- Aptitude and Interest tracks are never compared against each other.
- Children are never compared against siblings or other learners.

---

## 7. Strict Ownership & Authorization Enforcement

All dashboard, child profile, edit, delete, assessment continuation, and report views enforce strict ownership checks:

```python
if child.owner_id is None or child.owner_id != request.user.id:
    raise PermissionDenied("You are not authorized to access this child's profile.")
```

- Unauthenticated visitors are redirected to `/login/?next=...`.
- User A cannot view User B's dashboard records, children, or reports.
- User A cannot edit or delete User B's children via URL manipulation.
- Unowned child profiles (`owner=None`) are strictly blocked with `403 Forbidden`.
- Session values (`active_child_id`) are never trusted as authorization tokens.

---

## 8. Database Migrations & Data Preservation

- **Database Migrations:** No schema migrations were required for Task 08. All functionality builds upon existing models and relationships (`Child.owner`, `Assessment.child`, `Result.assessment`).
- **Data Integrity:** All historical questions (150 total), historical assessments (3 total), and results (2 total) in `db.sqlite3` were 100% preserved.

---

## 9. Comprehensive Test Suite Results

The test suite in [`core/tests.py`](file:///e:/project/aptitude_finder/core/tests.py) was expanded with 21 new tests across 3 dedicated test classes, covering all requirements specified in Section 11:
- `DashboardViewTest`: 6 tests
- `ChildProfileAndManagementTest`: 9 tests
- `AssessmentHistoryAndComparisonTest`: 7 tests

### Test Execution:
```bash
python manage.py test
```

```
Ran 92 tests in 73.071s
OK
System check identified no issues (0 silenced).
```

All 92 tests passed with zero failures and zero errors.

---

## 10. Modified and Created Files

| File | Status | Description |
|---|---|---|
| `core/views.py` | **Modified** | Added `dashboard`, `child_detail`, `child_edit`, `child_delete`, and `child_add` views. |
| `core/urls.py` | **Modified** | Added URL routes for dashboard and child management. |
| `assessment/views.py` | **Modified** | Updated `questionnaire_entry` to synchronize `active_child_id` in session on continuation. |
| `templates/base.html` | **Modified** | Added `Dashboard` navigation item for authenticated users. |
| `core/templates/core/dashboard.html` | **Created** | Parent dashboard with KPIs, children cards, and empty state. |
| `core/templates/core/child_detail.html` | **Created** | Child profile, track summaries, longitudinal comparisons, and history table. |
| `core/templates/core/child_edit.html` | **Created** | Child profile editing interface with validation. |
| `core/templates/core/child_confirm_delete.html` | **Created** | Safety confirmation screen with cascading impact summary. |
| `core/templates/core/child_add.html` | **Created** | Dashboard child registration interface. |
| `core/tests.py` | **Modified** | Added 21 automated unit tests covering all Task 08 requirements. |
| `TASK_08_COMPLETION_REPORT.md` | **Created** | Comprehensive task completion documentation. |

---

## 11. Known Limitations & Scope Alignment

- **Local Development Environment:** Powered by Django's native authentication and SQLite backend in alignment with B.Tech CSE semester project requirements.
- **Pure Native Technologies:** Built purely with Django templates, Django ORM, and custom CSS without introducing external JavaScript charting libraries, heavy single-page application frameworks, or asynchronous task queues.

