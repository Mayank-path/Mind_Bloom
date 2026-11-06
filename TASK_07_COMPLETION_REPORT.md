# MindBloom — Task 07 Completion Report: Age-Appropriate Assessment Design & Question Bank Enhancement

**Project:** MindBloom — Child Aptitude & Interest Assessment System  
**University Course:** B.Tech CSE Semester Project  
**Framework:** Django 5.2.19 (Python 3.11.9)  
**Database:** SQLite (`db.sqlite3`)  
**Completed:** November 2026  

---

## 1. Executive Summary

Task 07 significantly upgraded MindBloom's assessment engine from a uniform 30-question bank into an age-differentiated developmental assessment framework. Previously, children aged 5 through 18 were served identical questionnaires regardless of cognitive maturity, reading level, or problem-solving capability.

With Task 07, MindBloom now classifies learners into three distinct developmental tiers (`GROUP_1: Ages 5–8`, `GROUP_2: Ages 9–13`, `GROUP_3: Ages 14–18`), expands the active question bank fivefold from 30 to **150 structured questions** (75 Aptitude questions across 5 cognitive domains, 75 Interest exploration questions across 5 thematic domains), introduces standardized difficulty classification for Aptitude assessments, and prevents cross-age question leakage in the questionnaire workflow. Historical assessments completed prior to Task 07 remain fully functional, viewable, and statistically sound without schema breaks or database resets.

---

## 2. Age Group Classification Schema

### Developmental Tiers & Boundary Conditions
The age-group classification strictly enforces supported age limits between 5 and 18:

| Age Group Identifier | Age Range | Developmental Stage Label | Cognitive / Assessment Design Focus |
|---|---|---|---|
| `GROUP_1` | 5–8 years | Early Exploration | Visual reasoning, intuitive counting, everyday animal/nature associations, concrete scenarios, simple vocabulary. |
| `GROUP_2` | 9–13 years | Developing Reasoning | Multi-step problem solving, pattern extrapolation, arithmetic operations, spatial orientation, structured interests. |
| `GROUP_3` | 14–18 years | Advanced Exploration | Abstract logical deductions, algebraic relationships, 3D mental rotation, systemic problem solving, complex multidimensional interests. |

### Classification Helpers
Implemented in [`assessment/utils.py`](file:///e:/project/aptitude_finder/assessment/utils.py):
- `get_age_group(age)`: Validates that `age` is a valid integer between 5 and 18. Boundary handling:
  - $5 \le age \le 8 \implies \text{GROUP\_1}$
  - $9 \le age \le 13 \implies \text{GROUP\_2}$
  - $14 \le age \le 18 \implies \text{GROUP\_3}$
  - Raises `ValueError` for $age < 5$, $age > 18$, $age = \text{None}$, boolean types, or non-integer inputs.
- `get_age_group_label(age)`: Returns human-friendly stage labels (e.g., `"Early Exploration (Ages 5–8)"`).
- Connected directly to `Child` in [`core/models.py`](file:///e:/project/aptitude_finder/core/models.py) via `@property def age_group` and `@property def age_group_display`.

---

## 3. Model Enhancements & Database Migrations

### Model Adjustments in `assessment.Question`
In [`assessment/models.py`](file:///e:/project/aptitude_finder/assessment/models.py), the `Question` model was extended with two standardized `TextChoices` fields and updated ordering:
1. `age_group`:
   - `models.CharField(max_length=10, choices=AgeGroup.choices, default=AgeGroup.GROUP_2, db_index=True)`
   - Values: `GROUP_1`, `GROUP_2`, `GROUP_3`.
2. `difficulty`:
   - `models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM, db_index=True)`
   - Values: `EASY`, `MEDIUM`, `HARD`.
3. `Meta.ordering`:
   - Changed from `['order', 'id']` to `['age_group', 'order', 'id']`.

### Database Migrations
- Migration file created and applied: [`assessment/migrations/0003_alter_question_options_question_age_group_and_more.py`](file:///e:/project/aptitude_finder/assessment/migrations/0003_alter_question_options_question_age_group_and_more.py).
- Existing question rows in `db.sqlite3` safely received `age_group='GROUP_2'` and `difficulty='MEDIUM'` by default, preserving historical assessment integrity.

---

## 4. Question Bank Structure

The question repository contains exactly **150 unique, academically vetted questions**:

```
Total Questions: 150
├── Aptitude Track: 75 Questions
│   ├── GROUP_1 (Ages 5–8):   25 Questions (5 per category)
│   ├── GROUP_2 (Ages 9–13):  25 Questions (5 per category)
│   └── GROUP_3 (Ages 14–18): 25 Questions (5 per category)
└── Interest Track: 75 Questions
    ├── GROUP_1 (Ages 5–8):   25 Questions (5 per category)
    ├── GROUP_2 (Ages 9–13):  25 Questions (5 per category)
    └── GROUP_3 (Ages 14–18): 25 Questions (5 per category)
```

### Detailed Distribution Matrix

| Category Domain | GROUP_1 (5–8) | GROUP_2 (9–13) | GROUP_3 (14–18) | Category Total |
|---|---|---|---|---|
| **Aptitude: Logical Reasoning** | 5 | 5 | 5 | 15 |
| **Aptitude: Numerical Ability** | 5 | 5 | 5 | 15 |
| **Aptitude: Spatial Reasoning** | 5 | 5 | 5 | 15 |
| **Aptitude: Pattern Recognition** | 5 | 5 | 5 | 15 |
| **Aptitude: Problem Solving** | 5 | 5 | 5 | 15 |
| **Aptitude Subtotal** | **25** | **25** | **25** | **75** |
| **Interest: Science and Technology** | 5 | 5 | 5 | 15 |
| **Interest: Arts and Creativity** | 5 | 5 | 5 | 15 |
| **Interest: Social Activities** | 5 | 5 | 5 | 15 |
| **Interest: Nature and Exploration** | 5 | 5 | 5 | 15 |
| **Interest: Sports and Physical Activities** | 5 | 5 | 5 | 15 |
| **Interest Subtotal** | **25** | **25** | **25** | **75** |
| **Grand Total** | **50** | **50** | **50** | **150** |

### Question Quality Guarantees
- **Aptitude Questions:** Every question has a single verified `correct_option` (`A`, `B`, `C`, or `D`), 4 populated option choices, non-empty text, an assigned `difficulty`, and an active state.
- **Interest Questions:** Every question has `correct_option=None`, all 4 options independently mapped to distinct interest categories (`option_a_category` through `option_d_category`), no bias, and balanced options.

---

## 5. Seeding Strategy & Idempotency

### Data Population Architecture
Implemented in [`assessment/seed_data.py`](file:///e:/project/aptitude_finder/assessment/seed_data.py) and commanded by [`assessment/management/commands/seed_questions.py`](file:///e:/project/aptitude_finder/assessment/management/commands/seed_questions.py):
1. **Composite Key:** Questions are matched on `(assessment_type, age_group, order)`.
2. **In-Place Updates:** Existing questions in `db.sqlite3` (IDs 1–30) were matched with `GROUP_2` and updated in place. Foreign key references in completed `Answer` records were 100% preserved.
3. **Strict Idempotency Verification:**
   - First Execution: Created 120, Updated 30 (Total 150).
   - Subsequent Execution: Created 0, Updated 150 (Total 150).
   - Zero duplicate rows generated.

---

## 6. Assessment Flow & Questionnaire Adaptation

### Age-Scoping & Leakage Prevention
In [`assessment/views.py`](file:///e:/project/aptitude_finder/assessment/views.py) (`questionnaire_question` view):
- The question queryset dynamically filters by child developmental group:
  ```python
  child_age_group = assessment.child.age_group
  questions = list(
      Question.objects.filter(
          assessment_type=assessment.assessment_type,
          age_group=child_age_group,
          is_active=True
      ).order_by('order', 'id')
  )
  ```
- **Total Questions per Assessment:** Each child navigates 25 questions (1 through 25) instead of the previous 15.
- **Zero Leakage:** Children in `GROUP_1` are strictly isolated from `GROUP_2` or `GROUP_3` questions.
- **Premature Submission Prevention:** Submission is only valid on question 25. Answering question index < 25 redirects forward without finalizing.

---

## 7. Difficulty Classification & Presentation Rules

### Difficulty Distribution (Aptitude)
Across each age tier's 25 Aptitude questions:
- **Easy:** 8 questions (32%) — Foundational checks, building confidence.
- **Medium:** 12 questions (48%) — Core developmental reasoning.
- **Hard:** 5 questions (20%) — Multi-step cognitive challenges.

### Display & Scoring Constraints
- **Aptitude Display:** Renders a badge in the questionnaire header (e.g., `Difficulty: Easy`, `Difficulty: Medium`, `Difficulty: Hard`).
- **Interest Restriction:** **NEVER displayed** for Interest evaluations. Interest discovery has no "correct" or "difficult" answers; showing difficulty on interest items would induce social-desirability or test anxiety.
- Context injection in [`assessment/views.py`](file:///e:/project/aptitude_finder/assessment/views.py):
  ```python
  'difficulty_display': current_question.get_difficulty_display() if assessment.assessment_type == Assessment.AssessmentType.APTITUDE else None
  ```

---

## 8. Child Profile & UI Integration

1. **Assessment Selection Page** ([`assessment/templates/assessment/assessment_selection.html`](file:///e:/project/aptitude_finder/assessment/templates/assessment/assessment_selection.html)):
   - Displays the child's developmental tier badge alongside their name and age (e.g., `Developing Reasoning (Ages 9–13)`).
   - Clarifies that the upcoming assessments are tailored to their developmental age.
2. **Questionnaire Header** ([`assessment/templates/assessment/questionnaire.html`](file:///e:/project/aptitude_finder/assessment/templates/assessment/questionnaire.html)):
   - Displays `Question X of 25`.
   - Displays the stage badge (e.g., `Ages 5–8`).
   - Displays the difficulty badge only when `difficulty_display` is provided.

---

## 9. Results Calculation & Historical Compatibility

### Dynamic Scoring Services
In [`results/services.py`](file:///e:/project/aptitude_finder/results/services.py):
- `calculate_aptitude_result` and `calculate_interest_result` determine active expected questions by scoping to `assessment.child.age_group`.
- **Historical Assessment Compatibility:**
  ```python
  if assessment.status != Assessment.AssessmentStatus.COMPLETED and len(answers) < active_questions_count:
      raise ValueError("Cannot calculate results for an incomplete assessment.")
  ```
  If an assessment is marked `COMPLETED` (such as historical assessments with 15 questions created in Task 05/06), result calculation proceeds cleanly without raising `ValueError` and scales percentage calculations to recorded answers.
- **Exploratory Summary Phrasing:** Clarified summary text to be positive, educational, and constructive, eliminating clinical diagnosis terms.

---

## 10. Admin Configuration

In [`assessment/admin.py`](file:///e:/project/aptitude_finder/assessment/admin.py):
- `QuestionAdmin` includes `age_group` and `difficulty` in `list_display`, `list_filter`, and `search_fields`.
- Administrators and evaluators can filter questions by assessment type, age tier, category, and difficulty level.

---

## 11. Verification & Test Suite Summary

Full automated test suite executed via Django's test runner:

```bash
python manage.py test
```

### Results
- **Total Tests Run:** 70
- **Failures / Errors:** 0
- **Status:** OK
- **Execution Time:** ~65.4s

### Tested Capabilities & Edge Cases
1. `AgeGroupClassificationTest`:
   - Exact boundary mapping: 5, 8 $\to$ `GROUP_1`; 9, 13 $\to$ `GROUP_2`; 14, 18 $\to$ `GROUP_3`.
   - Rejections: 4, 19, 0, -1, 100, `None`, strings, floats, and booleans raise `ValueError`.
   - `Child.age_group` and `Child.age_group_display` properties.
2. `QuestionModelTest`:
   - Verification of 150 total questions (75 Aptitude, 75 Interest).
   - 25 questions per group per type across all 3 groups.
   - All 5 Aptitude categories present with correct options and difficulties.
   - All 5 Interest categories present with null correct options and valid option categories.
   - Filtering of inactive questions.
3. `QuestionnaireWorkflowTest`:
   - Loading question 1 of 25.
   - Age-group filtering: age 6 receives `GROUP_1`, age 16 receives `GROUP_3`, with zero question ID overlap.
   - Difficulty badge present on Aptitude questionnaire, absent on Interest questionnaire.
   - Prevention of premature submission before question 25.
   - Full 25-question progression, answer recording, and submission.
4. `ResultModelAndServicesTest` & `ResultsViewsTest`:
   - Aptitude and Interest calculation accuracy on 25-question scales.
   - Historical completed assessment compatibility.
   - Strict ownership protection across users and unowned profiles.

---

## 12. Modified and Created Files

| File | Status | Description |
|---|---|---|
| `assessment/utils.py` | **Created** | Age group classification (`get_age_group`, `get_age_group_label`). |
| `core/models.py` | **Modified** | Added `age_group` and `age_group_display` properties on `Child`. |
| `assessment/models.py` | **Modified** | Added `AgeGroup`, `Difficulty` choices and fields on `Question`. |
| `assessment/migrations/0003_*.py` | **Created** | Django schema migration for `age_group` and `difficulty`. |
| `assessment/admin.py` | **Modified** | Added `age_group` and `difficulty` to `QuestionAdmin`. |
| `assessment/seed_data.py` | **Modified** | Complete 150-question bank (75 Aptitude + 75 Interest). |
| `assessment/management/commands/seed_questions.py` | **Modified** | Idempotent seeder with per-group statistics. |
| `assessment/views.py` | **Modified** | Scoped questions to child age group; added difficulty & stage context. |
| `assessment/templates/assessment/questionnaire.html` | **Modified** | Rendered age-group stage and Aptitude difficulty badges. |
| `assessment/templates/assessment/assessment_selection.html` | **Modified** | Displayed child developmental stage. |
| `results/services.py` | **Modified** | Scoped expected count by age group; added historical support. |
| `assessment/tests.py` | **Modified** | Added age classification tests, 25-question workflow, badge checks. |
| `results/tests.py` | **Modified** | Added historical assessment compatibility and scoring tests. |
| `TASK_07_COMPLETION_REPORT.md` | **Created** | Comprehensive task completion documentation. |

---

## 13. Academic Context & Educational Disclaimer

> [!IMPORTANT]
> **Educational & Exploratory Scope:**  
> MindBloom is developed as a B.Tech Computer Science and Engineering semester software project. It provides an encouraging, positive framework to help children and parents explore cognitive strengths and natural curiosities.
> 
> MindBloom is **not** a clinical diagnostic instrument, IQ test, psychological evaluation, or career-tracking engine. All question texts, difficulty gradings, and categorical summaries are intended solely for educational demonstration and constructive academic exploration.

