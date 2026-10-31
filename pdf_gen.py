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


def _contact_block(resume: dict) -> str:
    """
    Builds the contact line for the PDF, using mailto:/tel:/https anchors so
    email, phone, GitHub and LinkedIn render as CLICKABLE links.
    """
    parts: list[str] = []
    email = resume.get("email") or ""
    phone = resume.get("phone") or ""
    location = resume.get("location") or ""
    github = resume.get("github") or ""
    linkedin = resume.get("linkedin") or ""

    if email:
        parts.append(f'Email: <a href="mailto:{email}">{email}</a>')
    if phone:
        parts.append(f'Phone: <a href="tel:{phone}">{phone}</a>')
    if location:
        parts.append(f"Location: {location}")
    if github:
        parts.append(f'GitHub: <a href="{github}">{github}</a>')
    if linkedin:
        parts.append(f'LinkedIn: <a href="{linkedin}">{linkedin}</a>')

    return " | ".join(parts)


def render_resume_pdf_bytes(resume: dict, jd_text: str = "") -> bytes:
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
        Paragraph(_contact_block(resume), contact_style),
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

    # Job description — passed from the run that produced this resume.
    jd = " ".join((jd_text or resume.get("jd_text") or "").split())
    if jd:
        story.append(Paragraph("Job Description", section_style))
        story.append(Paragraph(jd, body_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()
