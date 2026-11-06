# assemble_report_md.py - Assembles the complete Markdown Report
import os
import report_text as rt
import report_chapters as rc

OUTPUT_MD = r"E:\project\aptitude_finder\FINAL_PROJECT_REPORT\MindBloom_Final_Project_Report.md"

md_content = f"""# {rt.TITLE}

### {rt.SUBTITLE}

---

**A Capstone Project Report Submitted in Partial Fulfillment of the Requirements for the Award of the Degree of**  
### {rt.DEGREE}

**Submitted By:**  
- **Name:** {rt.PLACEHOLDER_STUDENT}  
- **Roll Number / Registration ID:** {rt.PLACEHOLDER_ROLL}  

**Under the Guidance and Supervision of:**  
- **Project Supervisor:** {rt.PLACEHOLDER_SUPERVISOR}  

**Department:** {rt.PLACEHOLDER_DEPT}  
**Institution:** {rt.PLACEHOLDER_COLLEGE}  
**Academic Session:** {rt.ACADEMIC_YEAR}  

---

<div style="page-break-after: always;"></div>

# CERTIFICATE OF ORIGINAL WORK

{rt.CERTIFICATE_TEXT}

<div style="page-break-after: always;"></div>

# DECLARATION

{rt.DECLARATION_TEXT}

<div style="page-break-after: always;"></div>

# ACKNOWLEDGEMENTS

{rt.ACKNOWLEDGEMENTS_TEXT}

<div style="page-break-after: always;"></div>

# ABSTRACT

{rt.ABSTRACT_TEXT}

<div style="page-break-after: always;"></div>

# TABLE OF CONTENTS

- **Certificate of Original Work**
- **Declaration**
- **Acknowledgements**
- **Abstract**
- **List of Figures**
- **List of Tables**
- **Chapter 1: Introduction**
  - 1.1 Project Background
  - 1.2 Problem Statement
  - 1.3 Purpose and Objectives
  - 1.4 Project Scope and Boundaries (Non-Diagnostic Framing)
  - 1.5 Organization of the Report
- **Chapter 2: Literature Review & Related Work**
  - 2.1 Theoretical Foundations of Child Development
  - 2.2 Survey of Existing Systems
  - 2.3 Critical Gap Analysis
  - 2.4 The Rationale for MindBloom
- **Chapter 3: Software Requirements Specification (SRS)**
  - 3.1 User Characteristics & Personas
  - 3.2 Functional Requirements (FR-01 to FR-05)
  - 3.3 Non-Functional Requirements (NFR-01 to NFR-05)
  - 3.4 Hardware, Software, and Network Prerequisites
  - 3.5 System Constraints and Assumptions
- **Chapter 4: System Architecture & Design**
  - 4.1 Architectural Pattern: Django MTV
  - 4.2 High-Level System Architecture Diagram
  - 4.3 Data Flow Diagrams (Level 0 and Level 1 DFDs)
  - 4.4 Entity-Relationship Diagram (ERD)
  - 4.5 Use Case Diagram
- **Chapter 5: Database Design & Data Dictionary**
  - 5.1 Relational Schema Architecture
  - 5.2 Comprehensive Data Dictionary (Tables 1 to 6)
  - 5.3 Referential Integrity & Cascade Policies
- **Chapter 6: Detailed Module Implementation**
  - 6.1 Core Application Module (`core`)
  - 6.2 Assessment Engine Module (`assessment`)
  - 6.3 Results & Analytics Module (`results`)
  - 6.4 Longitudinal Progression Tracking
  - 6.5 Security & Authorization Hardening
- **Chapter 7: User Interface & Experience Design**
  - 7.1 Child-Centric Design Philosophy
  - 7.2 Design System & CSS Tokens
  - 7.3 System Interface Walkthrough & Captioned Screenshots (Figures 1 to 13)
- **Chapter 8: Verification & Testing**
  - 8.1 Testing Philosophy and Strategy
  - 8.2 Automated Test Execution Summary
  - 8.3 Test Case Execution Matrix (94 Tests)
  - 8.4 Django System Integrity Check
- **Chapter 9: Results & Discussion**
  - 9.1 Experimental Workflow Evaluation
  - 9.2 Assessment Scoring Accuracy
  - 9.3 Longitudinal Comparative Analysis (Aarav Sharma Case Study)
  - 9.4 System Usability & Performance Evaluation
- **Chapter 10: Limitations & Challenges Encountered**
  - 10.1 Technical Challenges and Architectural Solutions
  - 10.2 Developmental Scope vs. Clinical Constraints
  - 10.3 Assessment Format Limitations
- **Chapter 11: Future Enhancements**
  - 11.1 Dynamic Item Response Theory (IRT) & Adaptive Branching
  - 11.2 Interactive Multimedia & Gamified Question Formats
  - 11.3 Multi-Year Longitudinal Growth Trajectories
  - 11.4 Institutional & School Administration Portals
- **Chapter 12: Conclusion**
  - 12.1 Project Summary
  - 12.2 Practical & Pedagogical Contributions
  - 12.3 Concluding Remarks
- **References & Bibliography**
- **Appendix A: Installation, Configuration & Execution Guide**
- **Appendix B: Source Code Highlights & Key Algorithms**

<div style="page-break-after: always;"></div>

# LIST OF FIGURES

- **Figure 1:** Public MindBloom Landing Page & Navigation Header (`01_homepage.png`)
- **Figure 2:** User Account Registration Interface (`02_registration.png`)
- **Figure 3:** User Authentication & Login Interface (`03_login.png`)
- **Figure 4:** Authenticated Parent Workspace Dashboard (`04_parent_dashboard.png`)
- **Figure 5:** Child Profile Registration & Intake Form (`05_child_registration.png`)
- **Figure 6:** Comprehensive Child Profile View (`06_child_profile.png`)
- **Figure 7:** Age-Adaptive Assessment Track Selection (`07_assessment_selection.png`)
- **Figure 8:** Interactive Aptitude Questionnaire Player (`08_aptitude_questionnaire.png`)
- **Figure 9:** Interactive Interest Questionnaire Player (`09_interest_questionnaire.png`)
- **Figure 10:** Quantitative Aptitude Result Report (`10_aptitude_result_report.png`)
- **Figure 11:** Qualitative Interest Affinity Report (`11_interest_result_report.png`)
- **Figure 12:** Chronological Assessment History Table (`12_assessment_history.png`)
- **Figure 13:** Longitudinal Attempt Comparison & Differential Card (`13_longitudinal_attempt_comparison.png`)

<div style="page-break-after: always;"></div>

# LIST OF TABLES

- **Table 2.1:** Comparative Survey of Existing Psychometric and Assessment Platforms
- **Table 3.1:** Functional Requirements Specification Matrix
- **Table 3.2:** Non-Functional Requirements Specification Matrix
- **Table 5.1:** Data Dictionary: `auth_user` (Authentication Table)
- **Table 5.2:** Data Dictionary: `core_child` (Child Demographic Profiles)
- **Table 5.3:** Data Dictionary: `assessment_assessment` (Assessment Attempt Sessions)
- **Table 5.4:** Data Dictionary: `assessment_question` (Tiered Question Bank)
- **Table 5.5:** Data Dictionary: `assessment_answer` (Recorded Response Table)
- **Table 5.6:** Data Dictionary: `results_result` (Synthesized Analytical Reports)
- **Table 8.1:** Automated Test Suite Results Breakdown by Application Module
- **Table 8.2:** Comprehensive Test Case Execution Matrix (94 Automated Test Cases)
- **Table 9.1:** Longitudinal Cognitive Domain Progression (Aarav Sharma Case Study)

<div style="page-break-after: always;"></div>

{rc.CHAPTER_1}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_2}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_3}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_4}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_5}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_6}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_7}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_8}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_9}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_10}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_11}

<div style="page-break-after: always;"></div>

{rc.CHAPTER_12}

<div style="page-break-after: always;"></div>

{rc.REFERENCES}

<div style="page-break-after: always;"></div>

{rc.APPENDIX_A}

<div style="page-break-after: always;"></div>

{rc.APPENDIX_B}
"""

with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"MindBloom_Final_Project_Report.md generated successfully! Size: {os.path.getsize(OUTPUT_MD)} bytes")
