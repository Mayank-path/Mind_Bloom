import os
import subprocess
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

REPORT_DIR = r"E:\project\aptitude_finder\FINAL_PROJECT_REPORT"
SCREENSHOTS_DIR = os.path.join(REPORT_DIR, "SCREENSHOTS")
MD_PATH = os.path.join(REPORT_DIR, "MindBloom_Final_Project_Report.md")
DOCX_PATH = os.path.join(REPORT_DIR, "MindBloom_Final_Project_Report.docx")
HTML_PATH = os.path.join(REPORT_DIR, "MindBloom_Final_Project_Report.html")
PDF_PATH = os.path.join(REPORT_DIR, "MindBloom_Final_Project_Report.pdf")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print("Script template ready.")
