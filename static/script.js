const ICONS = { tool: "🔧", decision: "🧠", conflict: "⚠️", verify: "✅", info: "▫️" };

let skillsTaxonomy = [];
let defaultData = null;
let lastResume = null;
let lastJdTitle = "";

async function init() {
  const res = await fetch("/api/demo-data");
  const data = await res.json();
  skillsTaxonomy = data.skills_taxonomy;
  defaultData = data;
}

function loadDemoExample() {
  if (!defaultData) return;
  document.getElementById("cand-name").value = defaultData.candidate.name;
  document.getElementById("cand-skills").value = defaultData.candidate.verified_skills.join(", ");

  const projectLines = defaultData.candidate.projects
    .map((p) => `${p.title} — ${p.description}`)
    .concat(defaultData.candidate.experience.map((e) => `${e.title} @ ${e.org} — ${e.description}`))
    .join("\n");
  document.getElementById("cand-projects").value = projectLines;

  document.getElementById("jd-title").value = defaultData.jd_title;
  document.getElementById("jd-company").value = defaultData.jd_company;
  document.getElementById("jd-text").value = defaultData.jd_text.trim();
}

// Detects which taxonomy skills appear in a piece of text (used to
// auto-tag each project/experience line the user typed in, so the agent's
// evidence-matching has something concrete to point to).
function detectSkills(text) {
  const lower = text.toLowerCase();
  return skillsTaxonomy.filter((s) => lower.includes(s.toLowerCase()));
}

function buildCandidateFromForm() {
  const name = document.getElementById("cand-name").value.trim() || "Candidate";
  const verifiedSkills = document.getElementById("cand-skills").value
    .split(",").map((s) => s.trim()).filter(Boolean);

  const projectLines = document.getElementById("cand-projects").value
    .split("\n").map((l) => l.trim()).filter(Boolean);

  const projects = projectLines.map((line) => {
    const [titlePart, ...descParts] = line.split("—");
    const title = (titlePart || "Project").trim();
    const description = (descParts.join("—") || "").trim() || title;
    return { title, description, skills: detectSkills(line) };
  });

  return {
    name,
    email: `${name.toLowerCase().replace(/\s+/g, ".")}@example.com`,
    phone: "N/A",
    location: "N/A",
    education: [],
    projects,
    experience: [],
    verified_skills: verifiedSkills,
  };
}

function renderLog(log) {
  const el = document.getElementById("log-entries");
  el.innerHTML = "";
  log.forEach((evt) => {
    const div = document.createElement("div");
    div.className = `log-entry ${evt.kind}`;
    div.innerHTML =
      `<div class="title">${ICONS[evt.kind] || ""} ${evt.actor.toUpperCase()} → ${evt.action}</div>` +
      `<div>${evt.detail}</div>`;
    el.appendChild(div);
  });
}

function renderState(data) {
  document.getElementById("state-summary").innerHTML =
    `<b>Stage:</b> ${data.stage}<br>` +
    `<b>Final status:</b> ${data.final_status}<br>` +
    `<b>Revisions made:</b> ${data.draft_versions.length - 1}`;

  const evalEl = document.getElementById("eval-history");
  evalEl.innerHTML = "";
  data.eval_history.forEach((ev) => {
    const badge = ev.passed ? "✅ PASSED" : "❌ FAILED";
    const flags = ev.fact_flags.length ? ` (flags: ${ev.fact_flags.join(", ")})` : "";
    const div = document.createElement("div");
    div.textContent = `v${ev.version}: ATS ${ev.ats_score}% — ${badge}${flags}`;
    evalEl.appendChild(div);
  });
}

async function runAgent() {
  const candidate = buildCandidateFromForm();
  const jdTitle = document.getElementById("jd-title").value.trim();
  const jdCompany = document.getElementById("jd-company").value.trim();
  const jdText = document.getElementById("jd-text").value.trim();
  const triggerConflict = document.getElementById("trigger-conflict").checked;

  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  btn.textContent = "Running...";

  const res = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate,
      jd_title: jdTitle || undefined,
      jd_company: jdCompany || undefined,
      jd_text: jdText || undefined,
      trigger_conflict: triggerConflict,
    }),
  });
  const data = await res.json();

  document.getElementById("results").style.display = "block";
  renderLog(data.log);
  renderState(data);

  lastResume = data.resume;
  lastJdTitle = data.jd_title;
  document.getElementById("pdf-btn").style.display = "inline-block";

  btn.disabled = false;
  btn.textContent = "▶ Run JivAI";
}

async function downloadPdf() {
  if (!lastResume) return;
  const res = await fetch("/api/render-pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume: lastResume, jd_title: lastJdTitle }),
  });
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${lastResume.name.replace(/\s+/g, "_")}_resume.pdf`;
  a.click();
}

document.getElementById("run-btn").addEventListener("click", runAgent);
document.getElementById("pdf-btn").addEventListener("click", downloadPdf);
document.getElementById("load-demo-btn").addEventListener("click", loadDemoExample);
init();