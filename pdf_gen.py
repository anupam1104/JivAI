"""
JivAI — renders a final verified resume dict into PDF bytes.
"""

import io
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors


def render_resume_pdf_bytes(resume: dict, jd_title: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle("NameStyle", parent=styles["Title"], fontSize=20,
                                 alignment=TA_LEFT, spaceAfter=2,
                                 textColor=colors.HexColor("#0f172a"))
    contact_style = ParagraphStyle("ContactStyle", parent=styles["Normal"], fontSize=9.5,
                                    textColor=colors.HexColor("#555555"), spaceAfter=10)
    section_style = ParagraphStyle("SectionStyle", parent=styles["Heading2"], fontSize=12,
                                    textColor=colors.HexColor("#1e3a5f"), spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=13.5)
    item_title_style = ParagraphStyle("ItemTitle", parent=styles["Normal"], fontSize=10.5,
                                       leading=13.5, fontName="Helvetica-Bold")

    story = [
        Paragraph(resume["name"], name_style),
        Paragraph(f"Applying for: {jd_title}", contact_style),
        Paragraph(resume["contact"], contact_style),
        HRFlowable(width="100%", color=colors.HexColor("#cccccc")),
        Paragraph("Summary", section_style),
        Paragraph(resume["summary"], body_style),
        Paragraph("Skills", section_style),
        Paragraph(", ".join(resume["skills"]) if resume["skills"] else "—", body_style),
        Paragraph("Experience", section_style),
    ]
    for e in resume.get("experience", []):
        story.append(Paragraph(f"{e['title']} — {e['org']} ({e['duration']})", item_title_style))
        story.append(Paragraph(e["description"], body_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Projects", section_style))
    for p in resume.get("projects", []):
        story.append(Paragraph(p["title"], item_title_style))
        story.append(Paragraph(p["description"], body_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Education", section_style))
    for ed in resume.get("education", []):
        story.append(Paragraph(
            f"{ed['degree']}, {ed['institution']} ({ed['year']}) — GPA {ed['gpa']}", body_style))

    doc.build(story)
    return buf.getvalue()