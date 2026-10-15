"""
report_generator.py
--------------------
Generates PDF and Excel reports directly from Python lists/dicts —
no pandas DataFrame needed. openpyxl writes Excel cell-by-cell, and
reportlab draws the PDF directly, which is a good way to see what
pandas' to_excel()/read_excel() are actually doing underneath.
"""

from pathlib import Path
from typing import Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def generate_pdf_report(scan: Dict) -> Path:
    filepath = REPORTS_DIR / f"tassie_report_{scan['id']}.pdf"
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Tassie — Secure Code Scan Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"File: {scan['filename']}", styles["Normal"]))
    elements.append(Paragraph(f"Scan date: {scan['created_at']}", styles["Normal"]))
    elements.append(Paragraph(f"Risk score: {scan['risk_score']} / 10", styles["Normal"]))
    elements.append(Spacer(1, 16))

    table_data = [["Line", "Category", "Severity", "Message"]]
    for f in scan["findings"]:
        table_data.append([
            str(f["line_number"]), f["category"], f["severity"], f.get("ai_explanation", f["message"])[:90]
        ])

    table = Table(table_data, colWidths=[40, 110, 60, 260])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#131a26")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(table)

    doc.build(elements)
    return filepath


def generate_excel_report(scan: Dict) -> Path:
    filepath = REPORTS_DIR / f"tassie_report_{scan['id']}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"

    headers = ["Line", "Category", "Severity", "Rule ID", "Message", "AI Explanation"]
    ws.append(headers)
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="131A26", end_color="131A26", fill_type="solid")

    for f in scan["findings"]:
        ws.append([
            f["line_number"], f["category"], f["severity"], f["rule_id"],
            f["message"], f.get("ai_explanation", "")
        ])

    for col_cells in ws.columns:
        length = max(len(str(c.value)) if c.value else 0 for c in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(length + 2, 60)

    wb.save(filepath)
    return filepath
