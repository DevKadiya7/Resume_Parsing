"""Predefined catalog of technical skills used for keyword matching.

This is intentionally a plain, curated list rather than an ML classifier —
Phase 2 explicitly avoids LLM/AI-API-based extraction. Matching is
case-insensitive and word-boundary-based (see
`app.services.extractors.skill_extractor`), so entries here should use
their canonical display casing (e.g. "PostgreSQL", not "postgresql").

Known limitation: a small number of skills (e.g. "Go", "R") are also
common English words/letters, so word-boundary matching can occasionally
produce a false positive on ordinary prose. This is an accepted
trade-off for a regex-based, non-ML matcher.
"""

_LANGUAGES = (
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C",
    "C++",
    "C#",
    "Go",
    "Rust",
    "Ruby",
    "PHP",
    "Swift",
    "Kotlin",
    "Scala",
    "R",
    "MATLAB",
    "Perl",
    "Dart",
    "Objective-C",
)

_WEB_FRONTEND = (
    "HTML",
    "CSS",
    "SASS",
    "React",
    "Angular",
    "Vue",
    "Next.js",
    "Nuxt.js",
    "Svelte",
    "jQuery",
    "Redux",
    "Tailwind CSS",
    "Bootstrap",
    "Webpack",
)

_WEB_BACKEND = (
    "FastAPI",
    "Flask",
    "Django",
    "Node.js",
    "Express",
    "Spring",
    "Spring Boot",
    "Ruby on Rails",
    "Laravel",
    "ASP.NET",
    ".NET",
    "NestJS",
    "GraphQL",
    "REST",
    "gRPC",
    "Microservices",
)

_DATABASES = (
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "SQLite",
    "Oracle",
    "Cassandra",
    "DynamoDB",
    "Elasticsearch",
    "MariaDB",
    "Neo4j",
    "Firebase",
)

_CLOUD_DEVOPS = (
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Ansible",
    "Jenkins",
    "CI/CD",
    "GitHub Actions",
    "GitLab CI",
    "Nginx",
    "Apache",
    "Linux",
    "Bash",
    "PowerShell",
    "Vagrant",
    "Prometheus",
    "Grafana",
)

_DATA_ML = (
    "TensorFlow",
    "PyTorch",
    "Keras",
    "Pandas",
    "NumPy",
    "Scikit-learn",
    "OpenCV",
    "NLTK",
    "spaCy",
    "Spark",
    "Hadoop",
    "Tableau",
    "Power BI",
    "Matplotlib",
    "Seaborn",
    "Jupyter",
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "Computer Vision",
)

_TOOLS_PRACTICES = (
    "Git",
    "GitHub",
    "GitLab",
    "Bitbucket",
    "JIRA",
    "Confluence",
    "Agile",
    "Scrum",
    "Kanban",
    "Selenium",
    "Pytest",
    "JUnit",
    "Postman",
    "Figma",
    "Excel",
)

SKILLS: tuple[str, ...] = tuple(
    sorted(
        {
            *_LANGUAGES,
            *_WEB_FRONTEND,
            *_WEB_BACKEND,
            *_DATABASES,
            *_CLOUD_DEVOPS,
            *_DATA_ML,
            *_TOOLS_PRACTICES,
        }
    )
)
