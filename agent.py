"""
JivAI — Autonomous Resume & Application Agent
agent.py: the core agent loop.

Workflow: parse JD -> research role -> check candidate evidence -> draft
resume -> evaluate (ATS + fact-consistency) -> REPLAN if evaluation fails
-> re-evaluate -> finalize or escalate.

This is the part that makes JivAI "agentic" rather than a single LLM call:
it maintains state across steps, takes an action, observes the result, and
changes its plan when that result is a failure.
"""

from __future__ import annotations
import time
import copy
from dataclasses import dataclass, field
from typing import Any

from data import SKILLS_TAXONOMY


# ---------------------------------------------------------------------------
# Persistent task state
# ---------------------------------------------------------------------------

@dataclass
class CaseState:
    stage: str = "initialized"
    jd_requirements: list[str] = field(default_factory=list)
    company_research: str = ""
    evidence_map: dict[str, Any] = field(default_factory=dict)
    draft_versions: list[dict] = field(default_factory=list)
    eval_history: list[dict] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    final_status: str | None = None  # "verified" | "escalated"

    def event(self, actor: str, action: str, detail: str, kind: str = "info"):
        """kind in {tool, decision, conflict, verify, info}"""
        self.log.append({
            "t": round(time.time(), 3),
            "actor": actor,
            "action": action,
            "detail": detail,
            "kind": kind,
        })


# ---------------------------------------------------------------------------
# TOOL 1: Parse job description -> extract required skills
#
# Real parsing, not a hardcoded list: scans the JD's raw text against
# SKILLS_TAXONOMY and keeps whichever taxonomy skills actually appear.
# ---------------------------------------------------------------------------

def parse_job_description(jd_text: str, state: CaseState) -> list[str]:
    text_lower = jd_text.lower()
    found = [skill for skill in SKILLS_TAXONOMY if skill.lower() in text_lower]

    state.jd_requirements = found
    state.event(
        "tool", "parse_job_description",
        f"Scanned JD text against {len(SKILLS_TAXONOMY)} known skills — "
        f"found {len(found)} required: {', '.join(found) if found else 'none'}.",
        kind="tool",
    )
    return found


# ---------------------------------------------------------------------------
# TOOL 2: Research role/company (kept deterministic/offline — zero API
# keys needed to run or deploy JivAI)
# ---------------------------------------------------------------------------

def research_role(jd_title: str, jd_company: str, jd_requirements: list[str],
                   state: CaseState) -> str:
    top_skills = ", ".join(jd_requirements[:4]) if jd_requirements else "general skills"
    blurb = (
        f"'{jd_title}' at {jd_company} appears to prioritize: {top_skills}. "
        f"The agent will tailor the resume to foreground genuine evidence "
        f"for these specific areas rather than padding with generic content."
    )
    state.company_research = blurb
    state.event("tool", "research_role", blurb, kind="tool")
    return blurb


# ---------------------------------------------------------------------------
# TOOL 3: Reconcile candidate evidence against JD requirements
#
# For each required skill, decide if the candidate has REAL evidence:
# either it's in verified_skills, or it's tagged on a specific project/exp.
# This is the safeguard that prevents fabrication downstream.
# ---------------------------------------------------------------------------

def get_candidate_evidence(candidate: dict, jd_requirements: list[str],
                            state: CaseState) -> dict:
    verified = set(candidate.get("verified_skills", []))

    evidence_sources = []
    for p in candidate.get("projects", []):
        evidence_sources.append((p["title"], set(p.get("skills", []))))
    for e in candidate.get("experience", []):
        evidence_sources.append((f"{e['title']} @ {e['org']}", set(e.get("skills", []))))

    evidence_map = {}
    for kw in jd_requirements:
        supported = kw in verified
        source = None
        if supported:
            for title, skills in evidence_sources:
                if kw in skills:
                    source = title
                    break
            if source is None:
                source = "Listed verified skill (no specific project tagged)"
        evidence_map[kw] = {"supported": supported, "source": source}

    supported_list = [k for k, v in evidence_map.items() if v["supported"]]
    unsupported_list = [k for k, v in evidence_map.items() if not v["supported"]]

    state.evidence_map = evidence_map
    state.event(
        "tool", "get_candidate_evidence",
        f"Verified {len(supported_list)}/{len(jd_requirements)} required skills against "
        f"candidate evidence. Unsupported: {', '.join(unsupported_list) if unsupported_list else 'none'}.",
        kind="tool",
    )
    return evidence_map


# ---------------------------------------------------------------------------
# TOOL 4: Draft resume
#
# Only ever draws from SUPPORTED skills — except when tempt_fabrication=True,
# which deliberately reproduces a realistic drafting mistake (adding one
# JD-desired but unverified skill) so evaluation can catch it. This is the
# required demonstrable failure/conflict scenario for judging.
# ---------------------------------------------------------------------------

def draft_resume(candidate: dict, jd_title: str, jd_company: str,
                  evidence_map: dict, state: CaseState, version: int,
                  tempt_fabrication: bool = False) -> dict:
    supported_skills = [k for k, v in evidence_map.items() if v["supported"]]
    unsupported_skills = [k for k, v in evidence_map.items() if not v["supported"]]

    # Every skill the candidate declared as verified is evidence-backed in
    # itself. Start from the JD-relevant supported skills and then append the
    # candidate's other real verified skills so the final resume never ends up
    # with an empty Skills section just because the JD keywords didn't align.
    candidate_skills = [s for s in (candidate.get("verified_skills") or []) if isinstance(s, str) and s.strip()]
    supported_set = set(supported_skills)
    skills_section = [s for s in candidate_skills if s in supported_set]
    skills_section += [s for s in candidate_skills if s not in supported_set]

    fabricated_claims: list[str] = []

    if tempt_fabrication and unsupported_skills:
        # Simulate an over-eager first draft: pick one JD-desired but
        # unverified skill and include it anyway.
        claim = unsupported_skills[0]
        skills_section.append(claim)
        fabricated_claims.append(claim)

    summary = (
        f"{candidate['name']} — applying for {jd_title} at {jd_company}. "
        f"Demonstrated, evidence-backed experience in "
        f"{', '.join(supported_skills[:5]) if supported_skills else 'relevant technologies'}"
        + (f", and {', '.join(fabricated_claims)}" if fabricated_claims else "")
        + "."
    )

    github = (candidate.get("github") or "").strip()
    linkedin = (candidate.get("linkedin") or "").strip()
    github_url = f"https://github.com/{github}" if github and not github.startswith(("http://", "https://")) else github
    linkedin_url = f"https://www.linkedin.com/in/{linkedin}" if linkedin and not linkedin.startswith(("http://", "https://")) else linkedin

    contact_parts = []
    if candidate.get("email"):
        contact_parts.append(f"Email: {candidate.get('email')}")
    if candidate.get("phone"):
        contact_parts.append(f"Phone: {candidate.get('phone')}")
    if candidate.get("location"):
        contact_parts.append(f"Location: {candidate.get('location')}")
    if github_url:
        contact_parts.append(f"GitHub: {github_url}")
    if linkedin_url:
        contact_parts.append(f"LinkedIn: {linkedin_url}")
    contact = " | ".join(contact_parts)

    resume = {
        "version": version,
        "name": candidate["name"],
        "contact": contact,
        "email": candidate.get("email") or "",
        "phone": candidate.get("phone") or "",
        "location": candidate.get("location") or "",
        "github": github_url,
        "linkedin": linkedin_url,
        "summary": summary,
        "skills": skills_section,
        "education": candidate.get("education", []),
        "projects": candidate.get("projects", []),
        "experience": candidate.get("experience", []),
        "fabricated_claims": fabricated_claims,
    }

    state.draft_versions.append(copy.deepcopy(resume))
    state.event(
        "agent", "draft_resume",
        f"Drafted resume v{version}."
        + (f" ⚠️ Included unverified claim(s): {', '.join(fabricated_claims)}"
           if fabricated_claims else " No unverified claims included."),
        kind="decision",
    )
    return resume


# ---------------------------------------------------------------------------
# TOOL 5: Evaluate — ATS relevance score + factual-consistency check
#
# This is the verification step. Both checks must pass for the resume to
# be considered "done."
# ---------------------------------------------------------------------------

def evaluate_resume(resume: dict, jd_requirements: list[str], evidence_map: dict,
                     state: CaseState, ats_threshold: float = 50.0) -> dict:
    resume_skills = set(resume["skills"])
    jd_set = set(jd_requirements)
    overlap = resume_skills & jd_set
    ats_score = round(100 * len(overlap) / max(len(jd_set), 1), 1)

    fact_flags = [
        s for s in resume["skills"]
        if s in evidence_map and not evidence_map[s]["supported"]
    ]
    fact_flags = sorted(set(fact_flags))

    passed = (ats_score >= ats_threshold) and (len(fact_flags) == 0)

    result = {
        "version": resume["version"],
        "ats_score": ats_score,
        "fact_flags": fact_flags,
        "passed": passed,
    }
    state.eval_history.append(result)

    if fact_flags:
        state.event(
            "tool", "evaluate_resume",
            f"v{resume['version']}: ATS score {ats_score}%. "
            f"❌ FACT-CONSISTENCY FAILURE — unverifiable claim(s): {', '.join(fact_flags)}. "
            f"Not backed by any verified skill or project/experience evidence.",
            kind="conflict",
        )
    else:
        state.event(
            "tool", "evaluate_resume",
            f"v{resume['version']}: ATS score {ats_score}%. "
            f"Factual-consistency check passed — every listed skill is evidence-backed.",
            kind="verify",
        )
    return result


# ---------------------------------------------------------------------------
# TOOL 6: Revise — the replanning action taken after a failed evaluation
# ---------------------------------------------------------------------------

def revise_resume(resume: dict, fact_flags: list[str], state: CaseState) -> dict:
    revised = copy.deepcopy(resume)
    revised["version"] = resume["version"] + 1
    revised["skills"] = [s for s in revised["skills"] if s not in fact_flags]
    revised["fabricated_claims"] = []

    for flag in fact_flags:
        revised["summary"] = revised["summary"].replace(f", and {flag}", "")
        revised["summary"] = revised["summary"].replace(f", {flag}", "")
        revised["summary"] = revised["summary"].replace(flag, "")
    revised["summary"] = " ".join(revised["summary"].split())  # clean extra spaces
    revised["summary"] = revised["summary"].replace(" .", ".")

    state.draft_versions.append(copy.deepcopy(revised))
    state.event(
        "agent", "revise_resume",
        f"Replanning: removed unverified claim(s) {', '.join(fact_flags)} from "
        f"v{resume['version']}, regenerated as v{revised['version']}.",
        kind="decision",
    )
    return revised


# ---------------------------------------------------------------------------
# Main orchestration loop
# ---------------------------------------------------------------------------

def run_agent(candidate: dict, jd_title: str, jd_company: str, jd_text: str,
              demo_trigger_conflict: bool = True, max_revisions: int = 2
              ) -> tuple[dict, CaseState]:
    state = CaseState()
    state.event("agent", "start", f"Target role: {jd_title} at {jd_company}.")

    state.stage = "parsing_jd"
    jd_requirements = parse_job_description(jd_text, state)

    state.stage = "researching_role"
    research_role(jd_title, jd_company, jd_requirements, state)

    state.stage = "gathering_evidence"
    evidence_map = get_candidate_evidence(candidate, jd_requirements, state)

    state.stage = "drafting"
    resume = draft_resume(candidate, jd_title, jd_company, evidence_map, state,
                           version=1, tempt_fabrication=demo_trigger_conflict)

    state.stage = "evaluating"
    result = evaluate_resume(resume, jd_requirements, evidence_map, state)

    revisions = 0
    while not result["passed"] and revisions < max_revisions:
        state.stage = "replanning"
        if result["fact_flags"]:
            resume = revise_resume(resume, result["fact_flags"], state)
        else:
            state.event(
                "agent", "revise_resume",
                "ATS score below threshold with no fact issues — no further "
                "truthful claims available to add.",
                kind="decision",
            )
            break
        state.stage = "evaluating"
        result = evaluate_resume(resume, jd_requirements, evidence_map, state)
        revisions += 1

    state.stage = "verified" if result["passed"] else "escalated"
    state.final_status = state.stage

    if result["passed"]:
        state.event(
            "agent", "finalize",
            f"Final resume v{resume['version']} verified: ATS {result['ats_score']}%, "
            f"0 unverifiable claims.",
            kind="verify",
        )
    else:
        state.event(
            "agent", "escalate",
            f"Could not reach a verified state after {revisions} revision(s) — "
            f"escalating to human review.",
            kind="conflict",
        )

    return resume, state