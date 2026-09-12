"""
JivAI — Autonomous Resume & Application Agent
data.py: skills taxonomy (used for JD keyword extraction + evidence matching)
and a default demo example (fallback for quick one-click demos / judging).

The candidate and job description are normally provided by the USER through
the frontend form — this file is not the source of truth for a specific
person, it's the knowledge base the agent uses to parse and verify.
"""

# The agent only "understands" skills in this taxonomy — i.e. it can only
# extract a skill from a JD, or verify a skill against evidence, if it's
# listed here. Expand this list as needed.
SKILLS_TAXONOMY = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust",
    "FastAPI", "Flask", "Django", "Express", "Spring Boot",
    "React", "Vue", "Angular", "Next.js",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
    "REST APIs", "GraphQL", "gRPC",
    "JWT", "OAuth",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "CI/CD",
    "Git", "Unit Testing", "Microservices",
    "Machine Learning", "NLP", "PyTorch", "TensorFlow", "Data Analysis",
    "Streamlit", "Power BI", "Tableau",
    "HTML", "CSS", "Data Visualization",
]


# ---------------------------------------------------------------------------
# Default demo example — used only when the user clicks "Load Demo Example"
# instead of filling the form themselves. Keeps a guaranteed-working demo
# path available even if you're low on time before judging.
# ---------------------------------------------------------------------------

DEFAULT_CANDIDATE = {
    "name": "Rohan Verma",
    "email": "rohan.verma.dev@example.com",
    "phone": "+91-90000-00000",
    "location": "Delhi, India",
    "education": [
        {
            "degree": "B.Tech in Computer Science",
            "institution": "NIT Delhi",
            "year": "2022 - 2026",
            "gpa": "8.4/10",
        }
    ],
    "projects": [
        {
            "title": "JivAI Task Tracker",
            "description": (
                "Built a task management REST API using FastAPI and PostgreSQL, "
                "with JWT-based authentication and Docker deployment."
            ),
            "skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs", "JWT", "Docker"],
        },
        {
            "title": "Review Sentiment Model",
            "description": (
                "Trained an NLP sentiment classifier using PyTorch on scraped "
                "product reviews, deployed via a Flask endpoint."
            ),
            "skills": ["Python", "PyTorch", "NLP", "Flask"],
        },
    ],
    "experience": [
        {
            "title": "Backend Intern",
            "org": "Fictional Cloudworks Pvt Ltd",
            "duration": "May 2025 - Jul 2025",
            "description": (
                "Contributed to a billing microservice, added Redis caching, "
                "wrote unit tests for the payments module."
            ),
            "skills": ["Redis", "Microservices", "Unit Testing", "Git"],
        }
    ],
    "verified_skills": [
        "Python", "FastAPI", "PostgreSQL", "REST APIs", "JWT", "Docker",
        "PyTorch", "NLP", "Flask", "Redis", "Microservices", "Unit Testing", "Git",
    ],
}

DEFAULT_JD_TEXT = """
Solstice Systems is hiring a Backend Software Engineer (New Grad).

Responsibilities:
- Design and build scalable REST APIs and microservices in Python
- Work with PostgreSQL and Redis for storage and caching
- Write unit tests and participate in code review
- Deploy and monitor services on Kubernetes and AWS

Requirements:
- Strong Python, FastAPI or Flask
- REST API design, JWT/OAuth
- PostgreSQL, Docker
- Kubernetes and AWS experience a strong plus
- Bonus: NLP or ML deployment experience
"""

DEFAULT_JD_TITLE = "Backend Software Engineer - New Grad"
DEFAULT_JD_COMPANY = "Solstice Systems (fictional demo company)"