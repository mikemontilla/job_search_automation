# Plan: Job Search Agent — Phase 1: CV & Profile Management

## Context

Agente conversacional de IA unificado que gestiona todo el proceso de búsqueda de empleo. Se construye por fases, comenzando con gestión de perfiles y generación de CVs. La arquitectura (un solo agente + herramientas modulares) está diseñada para que cada nuevo módulo (discovery, filtering, tracking, etc.) se integre agregando nuevas herramientas al mismo agente, sin cambiar la estructura central.

## CV Format Decision: HTML/CSS → PDF (WeasyPrint)

LaTeX descartado por sintaxis hostil para la IA. WeasyPrint es Python puro, maneja UTF-8 perfecto (acentos francés/español), Claude genera HTML/CSS de forma confiable. Una sola plantilla Jinja2 para los 3 idiomas.

---

## Architecture (unified, extensible)

```
CLI (main.py)
  └─ JobAgent (agent.py)  ←→  Anthropic SDK tool-use loop
        ├─ SessionManager (session.py)   — historial de mensajes + session_log.json
        ├─ ToolRouter (tools/router.py)  — despacha llamadas a herramientas
        │     ├─ [Phase 1] ProfileManager (tools/profile.py)
        │     ├─ [Phase 1] CVGenerator    (tools/cv_gen.py)
        │     ├─ [Phase 1] JobLoader      (tools/jobs.py)
        │     ├─ [Phase 2] JobDiscovery   (tools/discovery.py)   ← futuro
        │     ├─ [Phase 2] JobFilter      (tools/filtering.py)   ← futuro
        │     ├─ [Phase 3] Tracker        (tools/tracking.py)    ← futuro
        │     └─ [Phase 3] LinkedIn       (tools/linkedin.py)    ← futuro
        └─ prompts.py  — system prompt del asistente completo de búsqueda
```

**Escalar es simple:** cada nuevo módulo agrega un archivo en `tools/`, registra sus herramientas en `definitions.py` y `router.py`. El agente central no cambia.

---

## File Structure

```
src/agent/                    # ← nombre genérico, no cv_agent
  __init__.py
  main.py           # CLI con Rich (python -m agent)
  agent.py          # JobAgent: loop tool-use con Anthropic SDK
  session.py        # SessionManager: lista de mensajes + session_log.json
  prompts.py        # System prompt completo + plantilla proactiva de inicio
  config.py         # Rutas (pathlib), mapeo idioma→sección, constantes
  tools/
    __init__.py
    definitions.py  # Todos los esquemas JSON de herramientas (se amplía por fase)
    router.py       # dict tool_name → callable (se amplía por fase)
    profile.py      # [Phase 1] read_profile, update_profile_section
    cv_gen.py       # [Phase 1] generate_cv_pdf (Jinja2 + WeasyPrint)
    jobs.py         # [Phase 1] list_job_offers, load_job_description

data/templates/
  cv.html           # Plantilla Jinja2 HTML/CSS (A4, variable de color de acento)

data/
  session_log.json  # last_note, last_updated, lista recent_cvs

config/
  agent_config.yaml # modelo, temperatura, idioma por defecto, colores de acento

requirements.txt
.env                # ANTHROPIC_API_KEY (ya en .gitignore)
```

---

## Phase 1 Tools (6 herramientas)

| Herramienta | Propósito |
|---|---|
| `read_profile` | Lee el perfil completo o una sección. Inputs: `language` (en/es/fr), `section_key` (opcional) |
| `update_profile_section` | Reemplaza una sección en un archivo de idioma. Inputs: `language`, `section_key`, `new_content` |
| `list_job_offers` | Lista las ofertas en applications/ y application_data/ |
| `load_job_description` | Lee un job_description.md por ID/slug |
| `generate_cv_pdf` | Renderiza plantilla Jinja2 + WeasyPrint → PDF. Inputs: `language`, `job_slug`, `cv_data` |
| `save_session_note` | Guarda nota breve de la sesión en session_log.json |

**Regla:** `update_profile_section` se llama 3× por actualización (una por idioma). El system prompt instruye al agente a generar siempre las 3 traducciones antes de llamar la herramienta.

---

## Mapeo de Nombres de Sección (config.py)

```python
SECTION_HEADINGS = {
    "summary":      {"en": "Professional Summary",   "es": "Resumen Profesional",       "fr": "Résumé Professionnel"},
    "experience":   {"en": "Professional Experience","es": "Experiencia Profesional",   "fr": "Expérience Professionnelle"},
    "education":    {"en": "Education",              "es": "Formación Académica",        "fr": "Formation Académique"},
    "publications": {"en": "Academic Publications",  "es": "Publicaciones Académicas",  "fr": "Publications Académiques"},
    "skills":       {"en": "Technical Skills",       "es": "Habilidades Técnicas",      "fr": "Compétences Techniques"},
    "languages":    {"en": "Languages",              "es": "Idiomas",                   "fr": "Langues"},
    "interests":    {"en": "Professional Interests", "es": "Intereses Profesionales",   "fr": "Intérêts Professionnels"},
    "projects":     {"en": "Personal Projects",      "es": "Proyectos Personales",      "fr": "Projets Personnels"},
    "hobbies":      {"en": "Interests and Hobbies",  "es": "Intereses y Hobbies",       "fr": "Centres d'Intérêt et Loisirs"},
}
```

`profile.py` usa regex `## <heading>` hasta el siguiente `## ` (o EOF) para hacer slicing y reemplazo de secciones.

---

## Reglas del System Prompt

- Al iniciar sesión: hacer 2-3 preguntas proactivas sobre la semana (nuevas tareas, cursos, logros)
- Responder en el idioma del usuario; generar contenido del CV en el idioma objetivo del CV
- En cualquier actualización de perfil: actualizar siempre los 3 archivos de idioma
- En generación de CV: reordenar/reescribir bullet points existentes para coincidir con la oferta — nunca inventar experiencia
- Modelo: `claude-sonnet-4-6` (balance costo/calidad); configurable en `agent_config.yaml`

---

## Persistencia de Sesión

`data/session_log.json` guarda: `last_note` (≤200 chars), `last_updated` (fecha), lista `recent_cvs`. Sin historial completo — cada sesión inicia fresca con solo la nota inyectada.

---

## Dependencias

**Python (requirements.txt):**
```
anthropic>=0.40.0
weasyprint>=62.0
jinja2>=3.1.0
rich>=13.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
```

**Sistema (una sola vez):**
```
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libcairo2 fonts-liberation
```

---

## Orden de Implementación — Phase 1

- [ ] 1. `config.py` + `requirements.txt` (instalar dependencias)
- [ ] 2. `tools/profile.py` — read/update con regex; probar contra los .md reales
- [ ] 3. `tools/definitions.py` + `tools/router.py`
- [ ] 4. `session.py` + `prompts.py` + `agent.py` — loop tool-use principal
- [ ] 5. `data/templates/cv.html` — plantilla Jinja2 A4; probar con WeasyPrint
- [ ] 6. `tools/cv_gen.py` + `tools/jobs.py`
- [ ] 7. `main.py` — CLI con Rich
- [ ] 8. `config/agent_config.yaml`
- [ ] 9. Test end-to-end completo

---

## Verificación Final

- `python -m agent` → el agente saluda y hace preguntas proactivas
- "Terminé un curso avanzado de Docker esta semana" → los 3 archivos de perfil actualizados (`git diff`)
- "Genera un CV en francés para esta oferta: [pegar JD]" → PDF en `applications/<slug>/cv_fr.pdf`
- Abrir PDF → layout correcto, texto en francés, sin caracteres faltantes
