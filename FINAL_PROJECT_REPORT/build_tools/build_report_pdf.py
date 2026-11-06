# build_report_pdf.py - Compiles MindBloom_Final_Project_Report.pdf via Headless Chrome
import os
import re
import subprocess
import report_text as rt
import report_chapters as rc

REPORT_DIR = r"E:\project\aptitude_finder\FINAL_PROJECT_REPORT"
SCREENSHOTS_DIR = os.path.join(REPORT_DIR, "SCREENSHOTS")
HTML_OUT = os.path.join(REPORT_DIR, "MindBloom_Final_Project_Report.html")
PDF_OUT = os.path.join(REPORT_DIR, "MindBloom_Final_Project_Report.pdf")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def markdown_to_html(md_text):
    html = []
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_lines = []
    in_table = False
    table_lines = []
    
    while i < len(lines):
        line = lines[i]
        
        # Code block
        if line.startswith("```"):
            if in_code:
                code_str = "\n".join(code_lines)
                html.append(f'<pre><code>{code_str}</code></pre>')
                code_lines = []
                in_code = False
            else:
                in_code = True
                code_lines = []
            i += 1
            continue
            
        if in_code:
            code_lines.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            i += 1
            continue
            
        # Table
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines.append(line.strip())
            if i + 1 >= len(lines) or not (lines[i+1].strip().startswith("|") and lines[i+1].strip().endswith("|")):
                rows = []
                for tline in table_lines:
                    if re.match(r'^\|[\s\-:|]+\|$', tline):
                        continue
                    parts = [p.strip() for p in tline.strip('|').split('|')]
                    rows.append(parts)
                if rows:
                    html.append('<div class="table-container"><table>')
                    for r_idx, r in enumerate(rows):
                        html.append('<tr>')
                        tag = 'th' if r_idx == 0 else 'td'
                        for c in r:
                            # format bold inside cells
                            c_fmt = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', c)
                            html.append(f'<{tag}>{c_fmt}</{tag}>')
                        html.append('</tr>')
                    html.append('</table></div>')
                table_lines = []
            i += 1
            continue

        # Image: ![Caption](Path)
        img_match = re.match(r'^!\[(.*?)\]\((.*?)\)', line.strip())
        if img_match:
            caption, img_rel = img_match.groups()
            img_filename = os.path.basename(img_rel)
            img_path = os.path.join(SCREENSHOTS_DIR, img_filename).replace(os.sep, "/")
            fig_caption = caption
            if i + 1 < len(lines) and lines[i+1].strip().startswith("*Figure"):
                fig_caption = lines[i+1].strip().strip("*")
                i += 1
            html.append(f'<div class="figure-container"><img src="file:///{img_path}" alt="{caption}"><p class="figure-caption">{fig_caption}</p></div>')
            i += 1
            continue

        # Callout block
        if line.startswith(">"):
            c_text = line.lstrip("> ").strip()
            c_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', c_text)
            html.append(f'<div class="callout">{c_text}</div>')
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            title = line[2:].strip()
            html.append(f'<h1 class="chapter-title">{title}</h1>')
        elif line.startswith("## "):
            title = line[3:].strip()
            html.append(f'<h2 class="section-title">{title}</h2>')
        elif line.startswith("### "):
            title = line[4:].strip()
            html.append(f'<h3 class="subsection-title">{title}</h3>')
        elif line.startswith("- "):
            # Bullet list
            item_text = line[2:].strip()
            item_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item_text)
            html.append(f'<li>{item_text}</li>')
        elif line.strip() == "":
            pass
        else:
            p_text = line
            p_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p_text)
            p_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p_text)
            html.append(f'<p>{p_text}</p>')
        i += 1
    return "\n".join(html)

# Read assembled chapters
chapters = [
    rc.CHAPTER_1, rc.CHAPTER_2, rc.CHAPTER_3, rc.CHAPTER_4,
    rc.CHAPTER_5, rc.CHAPTER_6, rc.CHAPTER_7, rc.CHAPTER_8,
    rc.CHAPTER_9, rc.CHAPTER_10, rc.CHAPTER_11, rc.CHAPTER_12,
    rc.REFERENCES, rc.APPENDIX_A, rc.APPENDIX_B
]

chapters_html = []
for idx, ch in enumerate(chapters):
    chapters_html.append(f'<div class="page-chapter">{markdown_to_html(ch)}</div>')
    if idx < len(chapters) - 1:
        chapters_html.append('<div class="page-break"></div>')

all_body = "\n".join(chapters_html)

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MindBloom — Final Project Report</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 25mm 20mm 25mm 20mm;
    @top-right {{
      content: "MindBloom — Final B.Tech Project Report";
      font-size: 8.5pt;
      color: #64748b;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      color: #64748b;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
  }}

  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #1e293b;
    background: #ffffff;
    margin: 0;
    padding: 0;
  }}

  .page-break {{
    page-break-after: always;
    break-after: page;
  }}

  .cover-page {{
    text-align: center;
    padding-top: 50px;
    height: 90vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}

  .cover-title {{
    font-size: 26pt;
    font-weight: 800;
    color: #1e3a8a;
    line-height: 1.25;
    margin-bottom: 12px;
  }}

  .cover-subtitle {{
    font-size: 13pt;
    font-style: italic;
    color: #475569;
    margin-bottom: 40px;
  }}

  .cover-award {{
    font-size: 11pt;
    color: #334155;
    margin: 30px 0;
  }}

  .cover-degree {{
    font-size: 14pt;
    font-weight: 700;
    color: #1e3a8a;
    letter-spacing: 0.5px;
    margin-top: 8px;
  }}

  .cover-details {{
    font-size: 11pt;
    line-height: 1.8;
    color: #1e293b;
    margin-top: 40px;
  }}

  h1.chapter-title {{
    font-size: 18pt;
    font-weight: 700;
    color: #1e3a8a;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 16px;
    page-break-after: avoid;
  }}

  h2.section-title {{
    font-size: 13.5pt;
    font-weight: 700;
    color: #2563eb;
    margin-top: 20px;
    margin-bottom: 10px;
    page-break-after: avoid;
  }}

  h3.subsection-title {{
    font-size: 11.5pt;
    font-weight: 600;
    color: #0f172a;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}

  p {{
    margin: 0 0 10px 0;
    text-align: justify;
  }}

  li {{
    margin-bottom: 4px;
  }}

  .callout {{
    background-color: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 12px 16px;
    margin: 14px 0;
    font-size: 10pt;
    color: #1e3a8a;
    border-radius: 4px;
  }}

  pre {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    overflow-x: auto;
    line-height: 1.4;
    margin: 12px 0;
    page-break-inside: avoid;
  }}

  .table-container {{
    margin: 16px 0;
    page-break-inside: avoid;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
  }}

  th {{
    background-color: #1e3a8a;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #1e3a8a;
  }}

  td {{
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
    color: #334155;
  }}

  tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}

  .figure-container {{
    text-align: center;
    margin: 18px 0;
    page-break-inside: avoid;
  }}

  .figure-container img {{
    max-width: 95%;
    height: auto;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }}

  .figure-caption {{
    font-size: 9pt;
    font-style: italic;
    color: #64748b;
    margin-top: 6px;
    text-align: center;
  }}

  .front-matter-title {{
    font-size: 18pt;
    font-weight: 700;
    color: #1e3a8a;
    text-align: center;
    margin-bottom: 24px;
  }}

  .prelim-p {{
    font-size: 11pt;
    line-height: 1.8;
    text-align: justify;
  }}
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover-page">
  <div>
    <div class="cover-title">{rt.TITLE}</div>
    <div class="cover-subtitle">{rt.SUBTITLE}</div>
    <div class="cover-award">
      A Capstone Project Report Submitted in Partial Fulfillment of the Requirements<br>
      for the Award of the Degree of<br>
      <div class="cover-degree">BACHELOR OF TECHNOLOGY<br>IN COMPUTER SCIENCE AND ENGINEERING</div>
    </div>
  </div>
  
  <div class="cover-details">
    <strong>Submitted By:</strong><br>
    {rt.PLACEHOLDER_STUDENT} (Roll No: {rt.PLACEHOLDER_ROLL})<br><br>
    <strong>Under the Guidance of:</strong><br>
    {rt.PLACEHOLDER_SUPERVISOR}<br><br>
    {rt.PLACEHOLDER_DEPT}<br>
    {rt.PLACEHOLDER_COLLEGE}<br>
    Academic Session {rt.ACADEMIC_YEAR}
  </div>
</div>

<div class="page-break"></div>

<!-- CERTIFICATE -->
<h1 class="front-matter-title">CERTIFICATE OF ORIGINAL WORK</h1>
<div class="prelim-p" style="white-space: pre-line;">{rt.CERTIFICATE_TEXT}</div>

<div class="page-break"></div>

<!-- DECLARATION -->
<h1 class="front-matter-title">DECLARATION</h1>
<div class="prelim-p" style="white-space: pre-line;">{rt.DECLARATION_TEXT}</div>

<div class="page-break"></div>

<!-- ACKNOWLEDGEMENTS -->
<h1 class="front-matter-title">ACKNOWLEDGEMENTS</h1>
<div class="prelim-p" style="white-space: pre-line;">{rt.ACKNOWLEDGEMENTS_TEXT}</div>

<div class="page-break"></div>

<!-- ABSTRACT -->
<h1 class="front-matter-title">ABSTRACT</h1>
<div class="prelim-p">{rt.ABSTRACT_TEXT}</div>

<div class="page-break"></div>

<!-- MAIN CHAPTERS -->
{all_body}

</body>
</html>
"""

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"HTML generated at: {HTML_OUT} ({os.path.getsize(HTML_OUT)} bytes)")

# Compile to PDF using Chrome Headless
chrome_cmd = [
    CHROME_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={PDF_OUT}",
    f"file:///{HTML_OUT.replace(os.sep, '/')}"
]

print("Executing Chrome headless PDF generation...")
res = subprocess.run(chrome_cmd, capture_output=True, text=True)
if res.returncode == 0 and os.path.exists(PDF_OUT):
    print(f"MindBloom_Final_Project_Report.pdf generated successfully! Size: {os.path.getsize(PDF_OUT)} bytes")
else:
    print(f"Error compiling PDF: returncode={res.returncode}")
    print("Stderr:", res.stderr)
