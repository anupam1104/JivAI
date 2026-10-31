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
        Paragraph(resume.get("name") or "Candidate", name_style),
        Paragraph(f"Applying for: {jd_title}", contact_style),
        Paragraph(resume.get("contact") or "", contact_style),
        HRFlowable(width="100%", color=colors.HexColor("#cccccc")),
        Paragraph("Summary", section_style),
        Paragraph(resume.get("summary") or "—", body_style),
        Paragraph("Skills", section_style),
        Paragraph(", ".join(str(s) for s in (resume.get("skills") or [])) if (resume.get("skills")) else "—", body_style),
        Paragraph("Experience", section_style),
    ]
    for e in resume.get("experience") or []:
        story.append(Paragraph(f"{e.get('title') or '?'} — {e.get('org') or '?'} ({e.get('duration') or '?'})", item_title_style))
        story.append(Paragraph(e.get("description") or "—", body_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Projects", section_style))
    for p in resume.get("projects") or []:
        story.append(Paragraph(p.get("title") or "Project", item_title_style))
        story.append(Paragraph(p.get("description") or "—", body_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Education", section_style))
    for ed in resume.get("education") or []:
        story.append(Paragraph(
            f"{ed.get('degree') or '?'}, {ed.get('institution') or '?'} ({ed.get('year') or '?'}) — GPA {ed.get('gpa') or '—'}",
            body_style))

    doc.build(story)
    return buf.getvalue()