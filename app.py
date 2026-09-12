"""
JivAI — Flask backend.
Thin routing layer: takes candidate + JD input (from the user via the
frontend form, or the default demo), runs the agent loop, returns JSON.
"""

from flask import Flask, render_template, jsonify, request, send_file
import io

from agent import run_agent
from pdf_gen import render_resume_pdf_bytes
from data import (
    SKILLS_TAXONOMY,
    DEFAULT_CANDIDATE, DEFAULT_JD_TEXT, DEFAULT_JD_TITLE, DEFAULT_JD_COMPANY,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/demo-data")
def demo_data():
    """Lets the frontend offer a 'Load Demo Example' button."""
    return jsonify({
        "candidate": DEFAULT_CANDIDATE,
        "jd_title": DEFAULT_JD_TITLE,
        "jd_company": DEFAULT_JD_COMPANY,
        "jd_text": DEFAULT_JD_TEXT,
        "skills_taxonomy": SKILLS_TAXONOMY,
    })


@app.route("/api/run", methods=["POST"])
def run():
    """
    Body:
    {
      "candidate": { name, email, phone, location, education[], projects[],
                     experience[], verified_skills[] },
      "jd_title": str,
      "jd_company": str,
      "jd_text": str,
      "trigger_conflict": bool
    }
    Any missing field falls back to the default demo value, so the button
    always works even with a half-filled form during a rushed demo.
    """
    body = request.get_json(silent=True) or {}

    candidate = body.get("candidate") or DEFAULT_CANDIDATE
    jd_title = body.get("jd_title") or DEFAULT_JD_TITLE
    jd_company = body.get("jd_company") or DEFAULT_JD_COMPANY
    jd_text = body.get("jd_text") or DEFAULT_JD_TEXT
    trigger_conflict = body.get("trigger_conflict", True)

    resume, state = run_agent(
        candidate, jd_title, jd_company, jd_text,
        demo_trigger_conflict=trigger_conflict,
    )

    return jsonify({
        "resume": resume,
        "log": state.log,
        "stage": state.stage,
        "final_status": state.final_status,
        "eval_history": state.eval_history,
        "draft_versions": state.draft_versions,
        "jd_title": jd_title,
    })


@app.route("/api/render-pdf", methods=["POST"])
def render_pdf():
    body = request.get_json(silent=True) or {}
    resume = body.get("resume")
    jd_title = body.get("jd_title", "Target Role")

    if resume is None:
        return jsonify({"error": "No resume provided"}), 400

    pdf_bytes = render_resume_pdf_bytes(resume, jd_title)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{resume['name'].replace(' ', '_')}_resume.pdf",
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)