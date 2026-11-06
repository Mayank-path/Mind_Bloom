# build_report_docx.py - Generates MindBloom_Final_Project_Report.docx
import os
import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

import report_text as rt
import report_chapters as rc

DOCX_OUT = r"E:\project\aptitude_finder\FINAL_PROJECT_REPORT\MindBloom_Final_Project_Report.docx"
SCREENSHOTS_DIR = r"E:\project\aptitude_finder\FINAL_PROJECT_REPORT\SCREENSHOTS"

doc = Document()

# Set standard 1-inch margins
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    
    # Configure Header & Footer
    header = section.header
    hp = header.paragraphs[0]
    hp.text = "MindBloom — Child Aptitude & Interest Assessment System | B.Tech Project Report"
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.style.font.name = "Calibri"
    hp.style.font.size = Pt(8.5)
    hp.style.font.color.rgb = RGBColor(120, 140, 160)
    
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = "Department of Computer Science & Engineering | Academic Year 2025–2026"
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.style.font.name = "Calibri"
    fp.style.font.size = Pt(8.5)
    fp.style.font.color.rgb = RGBColor(140, 150, 160)

# Configure Base Styles
normal_style = doc.styles['Normal']
normal_style.font.name = 'Calibri'
normal_style.font.size = Pt(11)
normal_style.font.color.rgb = RGBColor(30, 41, 59)
normal_style.paragraph_format.line_spacing = 1.3
normal_style.paragraph_format.space_after = Pt(6)

def clean_xml_string(s):
    if not isinstance(s, str):
        return str(s)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_heading_1(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(16)
    h.paragraph_format.space_after = Pt(8)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(clean_xml_string(text))
    run.font.name = 'Calibri'
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(30, 58, 138) # Navy Blue
    return h

def add_heading_2(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(clean_xml_string(text))
    run.font.name = 'Calibri'
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(37, 99, 235) # Royal Blue
    return h

def add_heading_3(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(clean_xml_string(text))
    run.font.name = 'Calibri'
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(15, 23, 42) # Slate Dark
    return h

def add_callout(text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, "EFF6FF")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(clean_xml_string(text))
    run.font.name = 'Calibri'
    run.font.size = Pt(10.5)
    run.font.italic = True
    run.font.color.rgb = RGBColor(30, 58, 138)
    doc.add_paragraph() # spacing

def add_code_block(code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(clean_xml_string(code_text.strip()))
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph()

# ----------------- COVER PAGE -----------------
title_p = doc.add_paragraph()
title_p.paragraph_format.space_before = Pt(40)
title_p.paragraph_format.space_after = Pt(12)
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
trun = title_p.add_run(rt.TITLE)
trun.font.name = 'Calibri'
trun.font.size = Pt(22)
trun.font.bold = True
trun.font.color.rgb = RGBColor(30, 58, 138)

sub_p = doc.add_paragraph()
sub_p.paragraph_format.space_after = Pt(36)
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
srun = sub_p.add_run(rt.SUBTITLE)
srun.font.name = 'Calibri'
srun.font.size = Pt(13)
srun.font.italic = True
srun.font.color.rgb = RGBColor(71, 85, 105)

info_box = doc.add_paragraph()
info_box.paragraph_format.space_after = Pt(40)
info_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
irun = info_box.add_run("A Capstone Project Report Submitted in Partial Fulfillment of the Requirements\nfor the Award of the Degree of\n")
irun.font.size = Pt(11)
irun2 = info_box.add_run(f"BACHELOR OF TECHNOLOGY\nIN COMPUTER SCIENCE AND ENGINEERING\n")
irun2.font.size = Pt(13)
irun2.font.bold = True
irun2.font.color.rgb = RGBColor(30, 58, 138)

details_p = doc.add_paragraph()
details_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
details_p.paragraph_format.space_after = Pt(50)
drun = details_p.add_run(
    f"Submitted By:\n"
    f"{rt.PLACEHOLDER_STUDENT} (Roll No: {rt.PLACEHOLDER_ROLL})\n\n"
    f"Under the Guidance of:\n"
    f"{rt.PLACEHOLDER_SUPERVISOR}\n\n"
    f"{rt.PLACEHOLDER_DEPT}\n"
    f"{rt.PLACEHOLDER_COLLEGE}\n"
    f"Academic Session {rt.ACADEMIC_YEAR}"
)
drun.font.size = Pt(11)

doc.add_page_break()

# ----------------- CERTIFICATE -----------------
add_heading_1("CERTIFICATE OF ORIGINAL WORK")
p_cert = doc.add_paragraph(rt.CERTIFICATE_TEXT)
doc.add_page_break()

# ----------------- DECLARATION -----------------
add_heading_1("DECLARATION")
p_decl = doc.add_paragraph(rt.DECLARATION_TEXT)
doc.add_page_break()

# ----------------- ACKNOWLEDGEMENTS -----------------
add_heading_1("ACKNOWLEDGEMENTS")
p_ack = doc.add_paragraph(rt.ACKNOWLEDGEMENTS_TEXT)
doc.add_page_break()

# ----------------- ABSTRACT -----------------
add_heading_1("ABSTRACT")
for para in rt.ABSTRACT_TEXT.split("\n\n"):
    doc.add_paragraph(para)
doc.add_page_break()

# ----------------- TABLE OF CONTENTS -----------------
add_heading_1("TABLE OF CONTENTS")
toc_items = [
    ("Certificate of Original Work", "ii"),
    ("Declaration", "iii"),
    ("Acknowledgements", "iv"),
    ("Abstract", "v"),
    ("List of Figures", "vi"),
    ("List of Tables", "vii"),
    ("Chapter 1: Introduction", "1"),
    ("Chapter 2: Literature Review & Related Work", "7"),
    ("Chapter 3: Software Requirements Specification (SRS)", "13"),
    ("Chapter 4: System Architecture & Design", "20"),
    ("Chapter 5: Database Design & Data Dictionary", "28"),
    ("Chapter 6: Detailed Module Implementation", "35"),
    ("Chapter 7: User Interface & Experience Design", "44"),
    ("Chapter 8: Verification & Testing", "54"),
    ("Chapter 9: Results & Discussion", "64"),
    ("Chapter 10: Limitations & Challenges Encountered", "70"),
    ("Chapter 11: Future Enhancements", "74"),
    ("Chapter 12: Conclusion", "78"),
    ("References & Bibliography", "81"),
    ("Appendix A: Installation, Configuration & Execution Guide", "84"),
    ("Appendix B: Source Code Highlights & Key Algorithms", "88"),
]
tbl_toc = doc.add_table(rows=len(toc_items), cols=2)
tbl_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
for idx, (title, page) in enumerate(toc_items):
    c0 = tbl_toc.cell(idx, 0)
    c1 = tbl_toc.cell(idx, 1)
    c0.text = title
    c1.text = str(page)
    c0.paragraphs[0].paragraph_format.space_after = Pt(2)
    c1.paragraphs[0].paragraph_format.space_after = Pt(2)
    c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if "Chapter" in title or "References" in title or "Appendix" in title:
        c0.paragraphs[0].runs[0].font.bold = True
        c1.paragraphs[0].runs[0].font.bold = True
doc.add_page_break()

# ----------------- LIST OF FIGURES -----------------
add_heading_1("LIST OF FIGURES")
figures_list = [
    ("Figure 1", "Public MindBloom Landing Page & Navigation Header", "SCREENSHOTS/01_homepage.png"),
    ("Figure 2", "User Account Registration Interface", "SCREENSHOTS/02_registration.png"),
    ("Figure 3", "User Authentication & Login Interface", "SCREENSHOTS/03_login.png"),
    ("Figure 4", "Authenticated Parent Workspace Dashboard", "SCREENSHOTS/04_parent_dashboard.png"),
    ("Figure 5", "Child Profile Registration & Intake Form", "SCREENSHOTS/05_child_registration.png"),
    ("Figure 6", "Comprehensive Child Profile View", "SCREENSHOTS/06_child_profile.png"),
    ("Figure 7", "Age-Adaptive Assessment Track Selection", "SCREENSHOTS/07_assessment_selection.png"),
    ("Figure 8", "Interactive Aptitude Questionnaire Player", "SCREENSHOTS/08_aptitude_questionnaire.png"),
    ("Figure 9", "Interactive Interest Questionnaire Player", "SCREENSHOTS/09_interest_questionnaire.png"),
    ("Figure 10", "Quantitative Aptitude Result Report", "SCREENSHOTS/10_aptitude_result_report.png"),
    ("Figure 11", "Qualitative Interest Affinity Report", "SCREENSHOTS/11_interest_result_report.png"),
    ("Figure 12", "Chronological Assessment History Table", "SCREENSHOTS/12_assessment_history.png"),
    ("Figure 13", "Longitudinal Attempt Comparison & Progression Card", "SCREENSHOTS/13_longitudinal_attempt_comparison.png"),
]
tbl_figs = doc.add_table(rows=len(figures_list), cols=2)
tbl_figs.alignment = WD_TABLE_ALIGNMENT.CENTER
for idx, (fnum, fdesc, _) in enumerate(figures_list):
    c0 = tbl_figs.cell(idx, 0)
    c1 = tbl_figs.cell(idx, 1)
    c0.text = fnum
    c1.text = fdesc
    c0.paragraphs[0].runs[0].font.bold = True
    c0.paragraphs[0].paragraph_format.space_after = Pt(2)
    c1.paragraphs[0].paragraph_format.space_after = Pt(2)
doc.add_page_break()

# ----------------- LIST OF TABLES -----------------
add_heading_1("LIST OF TABLES")
tables_list = [
    ("Table 2.1", "Comparative Survey of Existing Psychometric and Assessment Platforms"),
    ("Table 3.1", "Functional Requirements Specification Matrix"),
    ("Table 3.2", "Non-Functional Requirements Specification Matrix"),
    ("Table 5.1", "Data Dictionary: auth_user (Authentication Records)"),
    ("Table 5.2", "Data Dictionary: core_child (Child Demographic Profiles)"),
    ("Table 5.3", "Data Dictionary: assessment_assessment (Assessment Attempt Sessions)"),
    ("Table 5.4", "Data Dictionary: assessment_question (Tiered Question Bank Table)"),
    ("Table 5.5", "Data Dictionary: assessment_answer (Recorded Response Table)"),
    ("Table 5.6", "Data Dictionary: results_result (Synthesized Analytical Reports)"),
    ("Table 8.1", "Automated Test Suite Results Breakdown by Application Module"),
    ("Table 8.2", "Comprehensive Test Case Execution Matrix (94 Automated Test Cases)"),
    ("Table 9.1", "Longitudinal Cognitive Domain Progression (Aarav Sharma Case Study)"),
]
tbl_tbls = doc.add_table(rows=len(tables_list), cols=2)
tbl_tbls.alignment = WD_TABLE_ALIGNMENT.CENTER
for idx, (tnum, tdesc) in enumerate(tables_list):
    c0 = tbl_tbls.cell(idx, 0)
    c1 = tbl_tbls.cell(idx, 1)
    c0.text = tnum
    c1.text = tdesc
    c0.paragraphs[0].runs[0].font.bold = True
    c0.paragraphs[0].paragraph_format.space_after = Pt(2)
    c1.paragraphs[0].paragraph_format.space_after = Pt(2)
doc.add_page_break()

# ----------------- PARSE & RENDER CHAPTERS -----------------
def render_markdown_section(md_text):
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_lines = []
    in_table = False
    table_lines = []
    
    while i < len(lines):
        line = lines[i]
        
        # Code block handler
        if line.startswith("```"):
            if in_code:
                add_code_block("\n".join(code_lines))
                code_lines = []
                in_code = False
            else:
                in_code = True
                code_lines = []
            i += 1
            continue
            
        if in_code:
            code_lines.append(line)
            i += 1
            continue
            
        # Table handler
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines.append(line.strip())
            # check if next line is also table
            if i + 1 >= len(lines) or not (lines[i+1].strip().startswith("|") and lines[i+1].strip().endswith("|")):
                # render table
                rows_data = []
                for tline in table_lines:
                    if re.match(r'^\|[\s\-:|]+\|$', tline):
                        continue # separator row
                    parts = [p.strip() for p in tline.strip('|').split('|')]
                    rows_data.append(parts)
                if rows_data:
                    num_cols = max(len(r) for r in rows_data)
                    tbl = doc.add_table(rows=len(rows_data), cols=num_cols)
                    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                    for r_idx, r_data in enumerate(rows_data):
                        for c_idx in range(num_cols):
                            val = r_data[c_idx] if c_idx < len(r_data) else ""
                            cell = tbl.cell(r_idx, c_idx)
                            cell.text = clean_xml_string(val)
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_after = Pt(2)
                            p.paragraph_format.line_spacing = 1.15
                            if r_idx == 0:
                                set_cell_shading(cell, "1E3A8A") # Navy Blue Header
                                set_cell_margins(cell, 100, 100, 120, 120)
                                for r in p.runs:
                                    r.font.bold = True
                                    r.font.color.rgb = RGBColor(255, 255, 255)
                            else:
                                if r_idx % 2 == 1:
                                    set_cell_shading(cell, "F8FAFC")
                                set_cell_margins(cell, 80, 80, 120, 120)
                                for r in p.runs:
                                    r.font.size = Pt(9.5)
                    doc.add_paragraph()
                table_lines = []
            i += 1
            continue

        # Image handler: ![Caption](Path)
        img_match = re.match(r'^!\[(.*?)\]\((.*?)\)', line.strip())
        if img_match:
            caption, img_rel = img_match.groups()
            img_filename = os.path.basename(img_rel)
            img_path = os.path.join(SCREENSHOTS_DIR, img_filename)
            if os.path.exists(img_path):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(4)
                p_img.add_run().add_picture(img_path, width=Inches(5.8))
                
                # Check next line for italic caption
                if i + 1 < len(lines) and lines[i+1].strip().startswith("*Figure"):
                    cap_text = lines[i+1].strip().strip("*")
                    p_cap = doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_cap.paragraph_format.space_after = Pt(12)
                    crun = p_cap.add_run(clean_xml_string(cap_text))
                    crun.font.italic = True
                    crun.font.size = Pt(9.5)
                    crun.font.color.rgb = RGBColor(71, 85, 105)
                    i += 1
            i += 1
            continue

        # Callout block: > **NOTICE:** text
        if line.startswith(">"):
            callout_text = line.lstrip("> ").strip()
            add_callout(clean_xml_string(callout_text))
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            add_heading_1(line[2:].strip())
        elif line.startswith("## "):
            add_heading_2(line[3:].strip())
        elif line.startswith("### "):
            add_heading_3(line[4:].strip())
        elif line.strip() == "":
            pass # ignore blank lines
        else:
            p = doc.add_paragraph()
            # simple bold replacement
            text = line
            parts = re.split(r'(\*\*.*?\*\*)', text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(clean_xml_string(part[2:-2]))
                    r.font.bold = True
                else:
                    p.add_run(clean_xml_string(part))
        i += 1

chapters = [
    rc.CHAPTER_1, rc.CHAPTER_2, rc.CHAPTER_3, rc.CHAPTER_4,
    rc.CHAPTER_5, rc.CHAPTER_6, rc.CHAPTER_7, rc.CHAPTER_8,
    rc.CHAPTER_9, rc.CHAPTER_10, rc.CHAPTER_11, rc.CHAPTER_12,
    rc.REFERENCES, rc.APPENDIX_A, rc.APPENDIX_B
]

for ch_idx, ch in enumerate(chapters):
    render_markdown_section(ch)
    if ch_idx < len(chapters) - 1:
        doc.add_page_break()

doc.save(DOCX_OUT)
print(f"MindBloom_Final_Project_Report.docx generated successfully! Size: {os.path.getsize(DOCX_OUT)} bytes")
