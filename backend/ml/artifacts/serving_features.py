"""Feature building for the exported resume classifier - GENERATED FILE.

Emitted by backend/ml/02_train_classifier.ipynb. Do not edit by hand; rerun
the notebook instead. Serving code imports this module rather than
reimplementing the logic, so training and inference cannot drift apart.

The model consumes features in this exact order:
    [TF-IDF vector] + [FEATURE_COLUMNS]
"""

import re

import pandas as pd

PROGRAMMING_LANGUAGES = ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'dart']
FRAMEWORKS = ['react', 'angular', 'vue', 'next.js', 'django', 'flask', 'fastapi', 'spring', 'spring boot', 'node.js', 'express', 'laravel', 'rails', '.net', 'svelte', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy']
CLOUD_DEVOPS = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'linux', 'nginx', 'prometheus', 'grafana', 'helm']
DATA_TOOLS = ['sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'spark', 'hadoop', 'kafka', 'airflow', 'snowflake', 'dbt', 'tableau', 'power bi', 'databricks', 'hive']
FEATURE_COLUMNS = ['word_count', 'skill_count', 'language_count', 'framework_count', 'cloud_devops_count', 'data_tool_count', 'education_level', 'years_experience', 'certification_count', 'project_mentions', 'has_github']

_URL = re.compile(r"http\S+|www\.\S+")
_EMAIL = re.compile(r"\S+@\S+")
_NON_ALPHANUM = re.compile(r"[^a-z0-9+#./ ]")
_MULTI_SPACE = re.compile(r"\s+")
_YEARS_EXPERIENCE = re.compile(r"(\d{1,2})\s*\+?\s*years?")
_PROJECT_HINT = re.compile(r"\bprojects?\b")
_CERT_HINT = re.compile(r"\b(certified|certification|certificate)\b")

EDUCATION_LEVELS = [
    (r"\b(ph\.?d|doctorate)\b", 4),
    (r"\b(master|m\.?tech|m\.?sc|mba|mca)\b", 3),
    (r"\b(bachelor|b\.?tech|b\.?sc|b\.?e\.?|bca)\b", 2),
    (r"\b(diploma|associate)\b", 1),
]

def clean_resume(text: str) -> str:
    """Normalize resume text for vectorization.

    Keeps +, #, . and / so tokens like c++, c#, node.js and ci/cd survive.
    """
    text = str(text).lower()
    text = _URL.sub(" ", text)
    text = _EMAIL.sub(" ", text)
    text = _NON_ALPHANUM.sub(" ", text)
    return _MULTI_SPACE.sub(" ", text).strip()

def _count_terms(text: str, terms: list[str]) -> int:
    """Count how many of `terms` appear in `text` (word-boundary safe)."""
    return sum(1 for t in terms if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", text))

def build_engineered_features(texts: pd.Series) -> pd.DataFrame:
    """Derive 13 dense numeric features from cleaned resume text.

    Returns a DataFrame with one row per input text and a stable column
    order — the order is part of the saved artifact contract, so the
    serving code must build features in exactly this sequence.
    """
    rows = []
    for text in texts:
        words = text.split()
        word_count = len(words) or 1

        language_count = _count_terms(text, PROGRAMMING_LANGUAGES)
        framework_count = _count_terms(text, FRAMEWORKS)
        cloud_count = _count_terms(text, CLOUD_DEVOPS)
        data_count = _count_terms(text, DATA_TOOLS)
        skill_count = language_count + framework_count + cloud_count + data_count

        education_level = 0
        for pattern, level in EDUCATION_LEVELS:
            if re.search(pattern, text):
                education_level = level
                break

        years = [int(m) for m in _YEARS_EXPERIENCE.findall(text)]
        years_experience = min(max(years), 40) if years else 0

        rows.append({
            "word_count": word_count,
            "char_count": len(text),
            "skill_count": skill_count,
            "language_count": language_count,
            "framework_count": framework_count,
            "cloud_devops_count": cloud_count,
            "data_tool_count": data_count,
            "keyword_density": skill_count / word_count * 100,
            "education_level": education_level,
            "years_experience": years_experience,
            "certification_count": len(_CERT_HINT.findall(text)),
            "project_mentions": len(_PROJECT_HINT.findall(text)),
            "has_github": int("github" in text),
        })
    return pd.DataFrame(rows, index=texts.index)
