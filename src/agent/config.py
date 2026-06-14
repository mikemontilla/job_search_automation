from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

DATA_DIR = ROOT / "data"
RESUMES_DIR = DATA_DIR / "resumes"
TEMPLATES_DIR = DATA_DIR / "templates"
APPLICATIONS_DIR = ROOT / "applications"
CONFIG_DIR = ROOT / "config"
SESSION_LOG = DATA_DIR / "session_log.json"

PROFILE_FILES = {
    "en": RESUMES_DIR / "profile.md",
    "es": RESUMES_DIR / "perfil.md",
    "fr": RESUMES_DIR / "profil.md",
}

SECTION_HEADINGS = {
    "summary": {
        "en": "Professional Summary",
        "es": "Resumen Profesional",
        "fr": "Résumé Professionnel",
    },
    "experience": {
        "en": "Professional Experience",
        "es": "Experiencia Profesional",
        "fr": "Expérience Professionnelle",
    },
    "education": {
        "en": "Education",
        "es": "Formación Académica",
        "fr": "Formation Académique",
    },
    "publications": {
        "en": "Academic Publications",
        "es": "Publicaciones Académicas",
        "fr": "Publications Académiques",
    },
    "skills": {
        "en": "Technical Skills",
        "es": "Habilidades Técnicas",
        "fr": "Compétences Techniques",
    },
    "languages": {
        "en": "Languages",
        "es": "Idiomas",
        "fr": "Langues",
    },
    "interests": {
        "en": "Professional Interests",
        "es": "Intereses Profesionales",
        "fr": "Intérêts Professionnels",
    },
    "projects": {
        "en": "Personal Projects",
        "es": "Proyectos Personales",
        "fr": "Projets Personnels",
    },
    "hobbies": {
        "en": "Interests and Hobbies",
        "es": "Intereses y Hobbies",
        "fr": "Centres d'Intérêt et Loisirs",
    },
}

CV_TEMPLATE_DIR = TEMPLATES_DIR / "cv"
CV_TEMPLATE_HTML = CV_TEMPLATE_DIR / "CV Template.dc.html"
CV_TEMPLATE_JSON = CV_TEMPLATE_DIR / "profile.json"
