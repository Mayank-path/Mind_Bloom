# MindBloom — Child Aptitude & Interest Assessment System

**Academic Course:** B.Tech Computer Science & Engineering Semester Project  
**Technology Stack:** Python 3.11.9, Django 5.2.19, SQLite, HTML5, CSS3, Vanilla JavaScript  
**Architecture:** Django Model-View-Template (MVT) Pattern  

---

## 1. Project Overview

**MindBloom** is an educational web platform designed to identify, assess, and nurture children's cognitive aptitudes, reasoning capabilities, and intrinsic areas of interest. 

Unlike traditional scholastic evaluations that emphasize rote memorization and high-stakes test pressure, MindBloom provides a low-stress, positive self-discovery environment. The platform offers age-tailored questionnaires, dynamic scoring breakdowns, and constructive strength reports to empower parents and educators in guiding their children's learning pathways and extracurricular pursuits.

---

## 2. Problem Statement

Standard educational evaluations often focus exclusively on academic grades or uniform testing standards. This approach presents several challenges:
- **One-Size-Fits-All Assessments:** Children aged 5 to 18 possess vastly different cognitive maturities, vocabularies, and attention spans. Serving identical questions across age groups yields uninformative results.
- **Narrow Measurement Scope:** Traditional tests rarely measure multifaceted cognitive strengths (such as spatial orientation or pattern recognition) or intrinsic personal passions (such as creative arts or nature exploration).
- **Test Anxiety:** High-stakes grading frequently discourages children rather than fostering curious exploration.
- **Lack of Longitudinal Tracking:** Parents lack accessible tools to track how cognitive confidence and thematic curiosities develop over time.

---

## 3. Project Objectives

1. Develop a web application adhering to standard Django MVT design principles.
2. Implement an age-appropriate assessment engine calibrating questions into three developmental tiers:
   - **GROUP 1 (Ages 5–8):** Early Exploration (visual and intuitive reasoning).
   - **GROUP 2 (Ages 9–13):** Developing Reasoning (structured problem solving and multi-step deduction).
   - **GROUP 3 (Ages 14–18):** Advanced Exploration (abstract logic and multidimensional interests).
3. Create a dual-track assessment system:
   - **Cognitive Aptitude Track:** Objective questions across 5 core cognitive domains.
   - **Interest Discovery Track:** Preference-based questions across 5 exploratory domains.
4. Provide authenticated parents with a unified dashboard to manage multiple child profiles, review progress metrics, and track longitudinal score comparisons between attempts.
5. Enforce strict data privacy and ownership authorization so that child records and evaluation reports are accessible only by the verified parent.

---

## 4. Main Features

- **Parent & Educator Dashboard:** Central workspace displaying aggregated metrics, learner cards, and rapid assessment triggers.
- **Multi-Child Profile Management:** Support for registering, editing, and safely deleting multiple child profiles under a single parent account.
- **Age-Calibrated Question Bank:** 150 academically designed questions (75 Aptitude questions with difficulty badges and verified answer keys; 75 Interest exploration questions with balanced category mappings).
- **Interactive Questionnaire Engine:** One-question-at-a-time navigation, selectable radio options, progress tracking bar, answer persistence, and accidental submission guards.
- **Deterministic Result Generation:** Real-time scoring calculation for Aptitude (overall percentage and category breakdowns) and preference distribution for Interest.
- **Longitudinal Attempt Comparison:** Comparative progress tracking across multiple attempts of the same module, displaying score differences, category gains, and curiosity shifts.
- **Strict Authorization & Data Isolation:** Complete database isolation guaranteeing that unauthenticated visitors or other users cannot view or manipulate private child records.
- **Responsive Educational UI:** Pure CSS design system optimized for desktop, tablet, and mobile devices without third-party UI dependencies.

---

## 5. Technology Stack

| Layer | Component | Detail |
|---|---|---|
| **Language** | Python 3.11.9 | Core programming language |
| **Framework** | Django 5.2.19 | Full-stack web framework |
| **Database** | SQLite 3 | Relational database (`db.sqlite3`) |
| **Frontend** | HTML5, CSS3 | Semantic markup and custom responsive design tokens |
| **Interactivity** | Vanilla JavaScript | Client-side mobile drawer navigation toggle |
| **Testing** | Django Test Framework | 92 unit and integration tests |

---

## 6. Application Architecture

MindBloom is organized into three decoupled Django applications:

```text
aptitude_finder/
├── child_assessment/      # Core project configuration (settings, URLs, WSGI/ASGI)
├── core/                  # Authentication, parent dashboard, child profile management
│   ├── models.py          # Child model with age group classification properties
│   ├── views.py           # Dashboard, child CRUD views, authentication controllers
│   ├── forms.py           # Child and authentication forms
│   └── management/        # Demo dataset generator command
├── assessment/            # Questionnaire engine and question bank management
│   ├── models.py          # Assessment, Question, and Answer models
│   ├── utils.py           # Developmental age-group classification helpers
│   ├── views.py           # Questionnaire navigation and completion handlers
│   └── seed_data.py       # 150-question curated question bank
├── results/               # Result calculation engine and report rendering
│   ├── models.py          # Result model (category scores, distributions, summaries)
│   ├── services.py        # Scoring calculation algorithms for Aptitude and Interest
│   └── views.py           # Detailed visual report generation
├── templates/             # Global templates and custom error pages (403, 404, 500)
├── static/                # Master CSS stylesheet (style.css)
└── manage.py              # Django command-line utility
```

---

## 7. Database Model Overview

The database schema follows a strict relational structure:

```text
User (Django Built-in)
  │
  └── (1:N via Child.owner) ──► Child
                                  │
                                  ├── (1:N via Assessment.child) ──► Assessment
                                  │                                    │
                                  │                                    ├── (1:N) ──► Answer
                                  │                                    │
                                  │                                    └── (1:1) ──► Result
```

- **Child:** Name, age ($5 \le \text{age} \le 18$), gender, grade, owner foreign key, dynamic `@property age_group`.
- **Assessment:** Child foreign key, track type (`APTITUDE` or `INTEREST`), status (`PENDING` or `COMPLETED`), timestamps.
- **Question:** Assessment type, category, age group (`GROUP_1`, `GROUP_2`, `GROUP_3`), difficulty (`EASY`, `MEDIUM`, `HARD`), option texts, option categories, correct option.
- **Answer:** Assessment foreign key, question foreign key, selected option, correctness flag, contributed category.
- **Result:** Assessment one-to-one link, total questions, correct count, overall percentage, category scores JSON, preference distribution JSON, constructive feedback summary.

---

## 8. Installation & Setup Instructions

### Prerequisites
- Python 3.11.x installed on your operating system.
- Git (optional, for version management).

### Step 1: Navigate to Project Directory
```powershell
cd E:\project\aptitude_finder
```

### Step 2: Activate the Virtual Environment
Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(Or create a new environment if necessary: `python -m venv venv`)*

### Step 3: Verify Dependencies
Django 5.2.x is installed inside the virtual environment:
```powershell
python -m django --version
```

### Step 4: Run Database Migrations
Apply all schema migrations to SQLite:
```powershell
python manage.py migrate
```

### Step 5: Seed the Question Bank
Populate the 150-question curated assessment repository:
```powershell
python manage.py seed_questions
```
*(This command is strictly idempotent; running it multiple times updates existing questions without creating duplicates).*

### Step 6: Initialize Demonstration Dataset
To populate realistic demonstration data for academic evaluation:
```powershell
python manage.py setup_demo_data
```

### Step 7: Run the Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Access the application in your browser at: **`http://127.0.0.1:8000/`**

---

## 9. Demonstration Credentials

MindBloom includes a dedicated, pre-configured demonstration account:

| Field | Demonstration Account |
|---|---|
| **Role** | Parent / Educator |
| **Username** | `demo_parent` |
| **Password** | `DemoPass2026!` |
| **Email** | `parent@mindbloom.edu` |

### Pre-loaded Demonstration Data:
1. **Aarav Sharma (Age 10, GROUP 2):**
   - 2 Completed Aptitude Assessments (demonstrating longitudinal attempt score comparison and category progression).
   - 1 Completed Interest Assessment.
2. **Diya Sharma (Age 7, GROUP 1):**
   - 1 Completed Aptitude Assessment (Early Exploration tier).
   - 1 Completed Interest Assessment.
3. **Samarpan Roy (Age 11, GROUP 2):**
   - 1 Pending Aptitude Assessment (demonstrating the "Continue Assessment" workflow).

### How to Change the Demo Password
Log in as `demo_parent` and change the password via Django administration (`/admin/`) or run:
```powershell
python manage.py changepassword demo_parent
```

---

## 10. Key Application Routes

| URL Pattern | Name | Purpose | Access |
|---|---|---|---|
| `/` | `core:home` | Platform homepage & overview | Public |
| `/about/` | `core:about` | Educational philosophy & architecture | Public |
| `/contact/` | `core:contact` | Academic project inquiries | Public |
| `/login/` | `core:login` | Parent account login | Public |
| `/register/` | `core:register` | Parent account registration | Public |
| `/logout/` | `core:logout` | Account sign-out & session clearance | Authenticated |
| `/dashboard/` | `core:dashboard` | Parent workspace & statistics | Authenticated |
| `/dashboard/child/add/` | `core:child_add` | Quick child intake form | Authenticated |
| `/dashboard/child/<id>/` | `core:child_detail` | Child profile & longitudinal history | Authenticated (Owner) |
| `/dashboard/child/<id>/edit/` | `core:child_edit` | Edit child demographics | Authenticated (Owner) |
| `/dashboard/child/<id>/delete/`| `core:child_delete`| Safe delete confirmation screen | Authenticated (Owner) |
| `/assessment/` | `assessment:overview` | Assessment guide & tracks | Public |
| `/assessment/select/<child_id>/` | `assessment:selection` | Select Aptitude or Interest track | Authenticated (Owner) |
| `/assessment/<id>/take/` | `assessment:take` | Entrypoint to active questionnaire | Authenticated (Owner) |
| `/assessment/<id>/question/<n>/` | `assessment:question` | One-question questionnaire view | Authenticated (Owner) |
| `/assessment/<id>/complete/` | `assessment:completion` | Post-submission confirmation | Authenticated (Owner) |
| `/results/` | `results:overview` | Results overview portal | Authenticated |
| `/results/assessment/<id>/` | `results:assessment_report` | Detailed visual strength report | Authenticated (Owner) |

---

## 11. Automated Testing

MindBloom maintains a full automated regression test suite covering models, forms, scoring algorithms, access controls, and UI workflows:

```powershell
python manage.py test
```

### Test Coverage Summary:
- **Total Tests:** 92
- **Failures:** 0
- **Errors:** 0
- **Status:** OK

---

## 12. Educational Disclaimer & Scope

> **Academic Project Notice:** MindBloom is developed as an undergraduate B.Tech Computer Science & Engineering software engineering project. It is strictly an educational exploration tool designed to support positive reflection on learning styles and curiosities. MindBloom does not issue medical diagnoses, psychological metrics, IQ scores, or clinical evaluations.
