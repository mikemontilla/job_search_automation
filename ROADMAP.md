# Project Roadmap — Job Search Automation

Este archivo es la fuente de verdad del estado y la dirección del proyecto.

---

## Arquitectura General

```
CLI (main.py)
  └─ JobAgent (agent.py)  ←→  Anthropic SDK tool-use loop       [Phase 1 ✅]
        ├─ SessionManager (session.py)
        ├─ ToolRouter (tools/router.py)
        │     ├─ ProfileManager (tools/profile.py)              [Phase 1 ✅]
        │     ├─ CVGenerator    (tools/cv_gen.py)               [Phase 1 ✅]
        │     ├─ JobLoader      (tools/jobs.py)                 [Phase 1 ✅]
        │     ├─ DiscoveryTools (tools/discovery.py)            [Phase 2.3 ✅]
        │     └─ ApplicationTools (tools/applications.py)       [Phase 3.2 ✅]
        └─ prompts.py

src/discovery/  ←→  FastAPI web UI + SQLite store (offers)      [Phase 2 ✅]
src/tracking/   ←→  applications/events (mismo discovery.db) +  [Phase 3 ✅]
                    dashboard en el mismo servidor FastAPI
src/linkedin/   ←→  data/linkedin/ (snapshot + recs) +           [Phase 4 ⬜]
                    keywords desde offers de discovery (token-free)
```

**Regla de escalabilidad:** cada módulo nuevo agrega archivos en `src/`. Si necesita
exponerse al agente conversacional, registra herramientas en `tools/definitions.py` +
`tools/router.py`. El agente central no cambia.

**Punto de encuentro entre módulos:** `data/discovery.db` (SQLite). Discovery escribe `offers`;
tracking escribe `applications`/`application_events`; el agente conversacional lee ambos (tablas
disjuntas, mismo archivo). La carpeta `applications/<slug>/` es el punto de encuentro de archivos
(CVs, job description, prep docs).

---

## Phase 1 — CV Agent & Profile Management ✅ COMPLETADA

Agente conversacional con 6 herramientas para gestionar el perfil en 3 idiomas
(EN/ES/FR) y generar CVs en HTML tailored por oferta de trabajo.

**Cómo iniciarlo:**
```bash
python -m src.agent
```

**Archivos clave:**
- `src/agent/` — paquete completo del agente
- `data/resumes/profile.md` / `perfil.md` / `profil.md` — fuente de verdad del perfil
- `data/templates/cv/` — plantilla Claude Design HTML
- `config/agent_config.yaml` — modelo, idioma por defecto, fotos disponibles

**Pendientes (no urgente):**
- Mejoras al system prompt documentadas en `PLAN_cv_agent.md`
- El servidor FastAPI de Phase 2 puede reemplazar el workaround de base64 para servir CVs

---

## Phase 2 — Job Discovery System 🔄 EN PROGRESO

Pipeline determinista que busca, puntúa y almacena ofertas de trabajo.
La IA se usa **solo** en un paso acotado: extraer 16 campos estructurados + score de
compatibilidad por oferta nueva. Todo lo demás es determinista.

**Cómo iniciarlo:**
```bash
python -m src.discovery web          # interfaz web → http://127.0.0.1:8000
python -m src.discovery run          # ejecuta el pipeline (fuentes configuradas)
python -m src.discovery ingest "https://..."  # ingestar una URL manualmente
```

**Archivos clave:**
- `src/discovery/` — paquete completo
- `config/discovery_config.yaml` — modelo (haiku), umbral de score, fuentes, puerto
- `data/discovery.db` — store SQLite (gitignoreado)

### Pipeline

```
cron / "Run now" (web) / CLI
         │
         ▼
   sources/*.collect()  →  RawOffer(url, text, type)
         │
         ▼  [dedup: store.exists(id) — NO fetch ni IA si ya se vio]
         │
         ▼
   fetch.py  →  texto plano (httpx → Playwright si JS)
         │
         ▼
   scoring.py  →  1 llamada IA (haiku): 16 campos + score 0-100 + breakdown
         │
         ▼
   store.py (SQLite)  ←→  web/app.py (FastAPI + Jinja2 + htmx)
```

### Fase 2.0 — Fundación ✅ COMPLETADA (2026-06-14)

- [x] `config.py` + `config/discovery_config.yaml`
- [x] `models.py` — `Offer` dataclass + `OfferStatus` enum + dedup por hash de URL
- [x] `store.py` — SQLite: exists, upsert, list, set_status, delete soft
- [x] `fetch.py` — httpx + fallback Playwright (Chromium instalado)
- [x] `scoring.py` — tool-use forzado → JSON estructurado (16 campos + score)
- [x] `sources/base.py` + `sources/manual.py`
- [x] `pipeline.py`
- [x] `web/` — FastAPI + Jinja2 + htmx: lista, detalle, marcar, borrar, pegar URL, "Run now"
- [x] `__main__.py` — CLI: `run` / `ingest` / `web`
- [x] `.gitignore` actualizado

**Prueba en vivo:** ✅ confirmada por el usuario (2026-06-14) — ingest manual, score/breakdown
visibles en el browser, dedup funcionando. También se corrigió un bug real durante la prueba:
páginas SPA pesadas (ej. Workday) necesitaban esperar a que la red se asentara
(`page.wait_for_load_state("networkidle")`) en vez de un timeout fijo — ver `fetch.py`.

**Mejoras de usabilidad agregadas tras la prueba:**
- Indicador de carga (spinner) en el formulario de ingest mientras Claude procesa la oferta
- Tarjetas visuales de **Strengths / Gaps** (pros/cons) en la página de detalle, generadas
  por el mismo llamado de IA que hace el scoring

### Fase 2.1 — Fuentes automáticas: career pages ✅ COMPLETADA (2026-06-20)

- [x] `src/discovery/sources/career_page.py` — `CareerPageSource`: abre la página de listado
  con Playwright, extrae los links de oferta individuales con un `link_selector` CSS
  configurable (o un patrón de URL de respaldo si no se configura uno)
- [x] `discovery_config.yaml → sources[]` — cada entrada: `name`, `url` (con filtros ya
  aplicados), `link_selector` opcional
- [x] `pipeline._configured_sources()` — construye las fuentes desde la config; `run()` ya
  no es un no-op
- [x] `fetch.goto_and_settle()` extraído como helper compartido (mismo wait robusto que el
  fix de Workday, reutilizado para listas y para páginas de detalle)
- [x] Probado contra fuentes reales: Siemens/Avature (server-rendered, solo httpx) y NXP/Workday
  (SPA JS, requiere Playwright) — ambos casos confirmados en producción
- [x] `src/discovery/sources/wp_ajax.py` — `WpAjaxJsonSource`: para sitios que filtran
  client-side vía POST a `wp-admin/admin-ajax.php` (ej. Serma/Zoho Recruit) en vez de cambiar
  la URL — llama el endpoint JSON directo, sin Playwright, con filtrado server-side (ahorra
  tokens de IA al no traer ofertas irrelevantes)
- [x] Configuradas 2 fuentes de Serma (`embarqué`, `image`) usando `type: wp_ajax`
- [x] Cron documentado en `README.md`

### Fase 2.2 — Alertas por email ✅ COMPLETADA (2026-06-20)

- [x] `src/discovery/gmail_auth.py` — OAuth2 de solo lectura (`gmail.readonly`), flujo
  interactivo único + cacheo/refresh de token (`config/gmail_token.json`, gitignored)
- [x] `src/discovery/sources/email_alerts.py` — `EmailAlertsSource`: busca correos de
  LinkedIn/Indeed, extrae links de oferta del HTML, canonicaliza (quita parámetros de
  tracking) antes del dedup — una misma oferta aparece con varios links distintos por correo
  (logo, título, botón) y sin canonicalizar se procesaría y puntuaría varias veces
- [x] CLI: `python -m src.discovery email-auth` (consentimiento inicial, requiere navegador)
- [x] `discovery_config.yaml → email` — `enabled`, `lookback_days`, `max_results`,
  `senders`/`link_patterns` opcionales
- [x] Probado en vivo contra la cuenta real del usuario: 7 ofertas únicas extraídas de
  alertas de LinkedIn, fetch + scoring + dedup confirmados end-to-end

### Fase 2.3 — Integración con el agente ✅ COMPLETADA (2026-06-20)

Herramientas de solo-lectura para el agente conversacional, en `src/agent/tools/discovery.py`:
- [x] `list_discovered_offers` — lista ofertas del store (filtros: status, recommended_only, limit)
- [x] `load_discovered_offer` — carga detalle completo (campos estructurados, breakdown, pros/cons,
  texto crudo) → usado para generar CV / preparar entrevista
- [x] `run_job_search` — dispara `pipeline.run()` desde el chat, sin esperar al cron

Registradas en `tools/definitions.py` + `tools/router.py`. El agente central (`agent.py`) no cambió.
Probado con datos reales del store: list/load funcionando, `run_job_search` confirmó dedup (0
ofertas nuevas, 36 ya conocidas, 0 errores) sin gastar tokens de IA.

---

## Phase 3 — Application Tracking & Interview Prep ✅ COMPLETADA (2026-06-21)

Fusiona los features 5/6/7 del documento de requerimientos original. Una **postulación
(application)** es el objeto central de esta fase: representa una oferta que Miguel está
persiguiendo activamente. Agrupa, bajo una misma carpeta `applications/<slug>/` y una fila en
la base de datos, todo lo que se va generando en el proceso — la oferta, los CVs por idioma,
los documentos de preparación de entrevista, la investigación de la empresa, los contactos de
RRHH y la línea de tiempo del proceso. El dashboard (3.1) da la vista de seguimiento; la
preparación de entrevistas (3.2) consume esos mismos documentos para producir material y
estrategia de nivel superior.

```
  Discovery offer (status=applying)          CV generado (Phase 1)
            │  "Promote to application"                │
            ▼                                          ▼
   ┌─────────────────────────────────────────────────────────┐
   │  applications/<slug>/   +   tabla `applications` (SQLite) │
   │    job_description.md          stage, hr_contact, fechas  │
   │    <lang>/cv.html              cv_languages, next_action  │
   │    prep/*.md                   timeline (application_events)│
   │    research/*.md                                          │
   └─────────────────────────────────────────────────────────┘
        ▲                                          │
        │  tracking dashboard (FastAPI)            │  agent tools (lectura/escritura)
        │  /applications                           ▼
   usuario triage                          Interview Prep & Strategy (agente)
```

**Decisión de almacenamiento:** las postulaciones viven en una tabla nueva `applications`
(+ `application_events`) dentro del **mismo** `data/discovery.db` (es el punto de encuentro ya
definido del proyecto). Módulos disjuntos: `src/discovery/` solo toca `offers`; el nuevo
`src/tracking/` solo toca `applications`/`application_events`. Una postulación puede referenciar
una oferta de discovery (`offer_id`) o ser standalone (postulación agregada a mano que nunca pasó
por el pipeline). El `status` de discovery (new/reviewed/applying/discarded) sigue siendo la señal
de triage gruesa; el `stage` de la postulación es el pipeline detallado del proceso.

### Modelo de datos (`src/tracking/store.py`, sobre `data/discovery.db`)

**Tabla `applications`:**
- `id` TEXT PK — el slug, coincide con el nombre de carpeta en `applications/`
- `offer_id` TEXT NULL — FK a `offers.id` si vino de discovery; NULL si es manual
- `title`, `company`, `location`, `source_url` — snapshot denormalizado (sobrevive aunque la
  oferta se descarte; soporta postulaciones manuales)
- `stage` TEXT — `interested` → `applied` → `screening` → `technical` → `final` → `offer` →
  `accepted` / `rejected` / `withdrawn`
- `cv_languages` TEXT (JSON) — idiomas de CV ya generados (se puede derivar escaneando la carpeta)
- `hr_contact` TEXT (JSON: name/email/phone/role)
- `applied_date`, `next_action`, `next_action_date`
- `notes` TEXT
- `created_at`, `updated_at`

**Tabla `application_events`** (línea de tiempo / historial):
- `id` INTEGER PK, `application_id` TEXT FK
- `event_type` TEXT — `stage_change` | `note` | `interview_scheduled` | `interview_done` |
  `document_added`
- `title`, `detail`, `event_date`, `created_at`

### Convención de carpeta (formaliza `applications/<slug>/`)

```
applications/<slug>/
  job_description.md     # texto de la oferta (de discovery.raw_text o pegado a mano)
  <lang>/cv.html, profile.json   # CVs ya generados por Phase 1
  prep/
    screening.md         # respuestas para llamada de screening / RH
    technical.md         # preguntas técnicas probables según stack/sector + respuestas guía
    questions_for_them.md# preguntas para hacerle al entrevistador
    strategy.md          # estrategia: qué destacar, cómo posicionar brechas, negociación
  research/
    company.md            # investigación de la empresa (opcional, lo agrega el usuario o el agente)
    interviewer_<slug>.md # perfil de cada entrevistador conocido (rol, trayectoria, intereses, temas en común)
```

**Investigación de entrevistadores:** cuando se agenda una entrevista (`application_events` con
`event_type=interview_scheduled`), el `detail` debe poder llevar la lista de participantes
(`[{name, role, linkedin_url?}]`, JSON). Antes de redactar `prep/technical.md` o
`prep/questions_for_them.md`, el agente usa esos nombres/roles — y cualquier perfil público que el
usuario le pase o que pueda buscar — para escribir `research/interviewer_<slug>.md` por persona
(trayectoria, rol actual, posibles puntos en común o temas técnicos de interés). Las preguntas y
respuestas guía generadas después combinan esa investigación con la oferta y el perfil de Miguel,
en vez de basarse solo en el texto de la oferta.

### 3.1 — Tracking store + dashboard web

- [x] `src/tracking/models.py` — `Application` dataclass + `ApplicationStage` enum + `ApplicationEvent`
- [x] `src/tracking/store.py` — esquema (migración idempotente como en discovery), CRUD:
  `upsert`, `get`, `list_applications(stage?)`, `set_stage`, `add_event`, `list_events`
- [x] `src/tracking/service.py` — `promote_offer(offer_id) -> Application`: crea la fila + la
  carpeta `applications/<slug>/` + escribe `job_description.md` desde `offer.raw_text`, marca la
  oferta como `applying`, y registra el evento inicial. Genera el slug desde company+title.
- [x] Rutas FastAPI nuevas en `src/discovery/web/app.py` (mismo servidor):
  - `GET /applications` — dashboard: tabla/columnas por `stage`, filtros, próxima acción
  - `GET /applications/{id}` — detalle: metadata editable, timeline, links a CVs y a `prep/*.md`
  - `POST /applications` — crear (promover desde oferta, o manual)
  - `POST /applications/{id}/stage` — cambiar etapa (registra `stage_change` event)
  - `POST /applications/{id}/event` — agregar nota / evento de entrevista
  - servir/visualizar archivos de la carpeta (CV, prep docs) renderizando markdown
- [x] Botón **"Promote to application"** en `detail.html` de la oferta de discovery
- [x] Templates: `applications.html`, `application_detail.html`, reutilizando el CSS existente
- [x] Nav entre las dos vistas (Discovery ↔ Applications) en `base.html`

### 3.2 — Preparación de entrevistas y estrategia (agente)

El agente lee **todos** los documentos que se han ido generando para la postulación (job
description, CV adaptado, notas de tracking, investigación, eventos previos) más el breakdown de
compatibilidad que ya calculó discovery (`score`, `pros`/`cons`, `rationale`, `breakdown`), y con
ese contexto produce material y estrategia de nivel superior.

- [x] `src/agent/tools/applications.py` — herramientas de lectura/escritura sobre la postulación:
  - `list_applications(stage?)` — lista postulaciones del store
  - `load_application(app_id)` — metadata + inventario de archivos de la carpeta + contenido de
    `job_description.md` + prep existente + (vía Phase 2.3) el `load_discovered_offer(offer_id)`
    asociado para traer score/pros/cons/rationale
  - `read_application_file(app_id, relpath)` — leer cualquier doc generado en la carpeta
  - `save_prep_document(app_id, kind, content_md)` — escribe en `prep/<kind>.md` y registra
    `document_added` event
  - `save_interviewer_research(app_id, slug, content_md)` — escribe en
    `research/interviewer_<slug>.md` y registra `document_added` event
  - `update_application(app_id, stage?, hr_contact?, notes?, next_action?)`
  - `log_application_event(app_id, type, title, detail, date)` — `detail` puede incluir la lista
    de entrevistadores (`interview_scheduled`) que dispara la investigación de cada uno
- [x] Registro en `tools/definitions.py` + `tools/router.py` (el agente central no cambia)
- [x] Prompt: nueva sección "Interview prep & strategy discipline" en `prompts.py` — flujo:
  cargar la postulación → leer todos sus documentos → identificar nivel de entrevista (screening
  vs técnica vs final) → si hay entrevistadores registrados sin investigación aún, el agente NO
  busca por sí mismo (no tiene acceso a internet): le sugiere a Miguel qué y dónde buscar
  (LinkedIn, página de equipo de la empresa, GitHub/publicaciones) y guarda lo que él reporte con
  `save_interviewer_research` → genera el doc correspondiente (combinando oferta + perfil de
  Miguel + investigación de entrevistadores) → lo guarda en `prep/` → resume a Miguel
- [x] Estrategia: el agente sintetiza, a partir de `pros`/`cons`/`rationale` + perfil + oferta,
  qué fortalezas destacar, cómo mitigar brechas, y ángulos de posicionamiento/negociación →
  `prep/strategy.md`

### Integraciones con los demás componentes

| Desde | Hacia | Mecanismo |
|---|---|---|
| Discovery (oferta `applying`) | Tracking | `promote_offer()` siembra la postulación + `job_description.md` |
| CV gen (Phase 1) | Tracking | `cv_languages` se deriva escaneando `applications/<slug>/<lang>/cv.html` (sin acoplar) |
| Tracking | Agente (3.2) | tools en `src/agent/tools/applications.py` leen la carpeta + el store |
| Discovery (Phase 2.3) | Agente (3.2) | `load_discovered_offer` aporta score/pros/cons/rationale al prep |
| Agente (3.2) | Tracking | `save_prep_document` / `log_application_event` escriben de vuelta en la postulación |

### Orden de implementación sugerido

1. `models.py` + `store.py` + migración (tablas vacías, probadas)
2. `service.promote_offer()` + formalización de carpeta (test: promover una oferta real)
3. Dashboard web (list + detail + stage + timeline) integrado en el FastAPI existente
4. Tools de agente para postulaciones (list/load/update/log_event) — probadas vía `dispatch`
5. Generación de prep + estrategia + prompt (test end-to-end con una oferta descubierta real)

---

## Phase 4 — LinkedIn Optimization ⬜ PENDIENTE (planeada)

**Objetivo:** ayudar a Miguel a optimizar su perfil de LinkedIn para que (a) sea consistente
con y esté enriquecido por los perfiles `.md` (fuente de verdad en `data/resumes/`), (b) use las
palabras clave que buscan los reclutadores del mercado objetivo —derivadas de las ofertas reales
que ya recoge discovery—, y (c) posicione mejor sus fortalezas de cara a las empresas a las que se
postula. La optimización es **generativa y conversacional** (como el interview prep de Fase 3), no
un pipeline determinista: reusa el agente existente.

**Decisión clave — sin scraping ni login automatizado.** LinkedIn prohíbe el scraping en sus ToS
y puede banear cuentas incluso con sesión autenticada. En vez de un navegador headless logueado,
Miguel le pasa el contenido de su perfil al agente por una de dos vías: (1) pegar el texto de las
secciones, o (2) importar el export oficial de LinkedIn ("Get a copy of your data" → ZIP de CSVs).
Cero riesgo de cuenta, y suficiente porque optimizar el perfil es una actividad periódica y
deliberada, no un monitoreo en tiempo real.

```
  data/resumes/*.md  ──(fuente de verdad)──┐
                                            ▼
  Miguel: pega texto / export ZIP ──► data/linkedin/snapshot.md   (estado actual)
                                            │
  discovery offers (objetivo) ──► keywords.py: agrega skills/keywords más pedidos (sin tokens)
                                            │
                                            ▼
        Agente (tools/linkedin.py) ──► recommendations/<section>.md
        (headline, about, experience, skills, keywords)
                                            │
                                            ▼
                  Miguel copia/pega en LinkedIn
```

**Almacenamiento:** el snapshot y las recomendaciones viven en `data/linkedin/` (consistente con
`data/resumes/`). Es contenido personal → gitignore de `data/linkedin/*` salvo `.gitkeep` (misma
decisión que `applications/`). Los `.md` de `data/resumes/` siguen siendo la fuente de verdad del
contenido profesional; LinkedIn es una *proyección* de ese contenido en el estilo de la plataforma
(primera persona, atractivo, rico en keywords).

### Convención de datos (`data/linkedin/`)
```
data/linkedin/
  snapshot.md                  # perfil actual de LinkedIn (pegado o importado del export)
  recommendations/
    headline.md                # titular optimizado (220 car.) + variantes
    about.md                   # sección "Acerca de" reescrita
    experience.md              # bullets por puesto, con métricas y keywords
    skills.md                  # skills a agregar/reordenar/quitar (orden = los más buscados primero)
    keywords.md                # keywords del mercado objetivo a sembrar en el perfil
  posts/
    <slug>.md                  # borradores de publicaciones para construir presencia
```

### 4.1 — Entrada de datos + agregación de keywords (`src/linkedin/`, determinista)
- [x] `src/linkedin/service.py` — read/write del snapshot y de `recommendations/<section>.md`,
  inventario de archivos y resolución de rutas con guardia anti-traversal (espejo de
  `src/tracking/service.py`)
- [ ] `src/linkedin/keywords.py` — `target_keywords(scope="recommended")`: lee la tabla `offers`
  de discovery (recomendadas y/o `applying`), agrega y rankea por frecuencia `skills_required` +
  `skills_nice` + términos del título. Sin llamadas a IA (token-free), da una base de datos real de
  "qué pide el mercado objetivo"
- [ ] (opcional) `src/linkedin/import_export.py` — parsea el ZIP del export oficial de LinkedIn
  (`Profile.csv`, `Positions.csv`, `Skills.csv`, `Education.csv`, `Languages.csv`...) y lo aplana a
  `snapshot.md`. La vía de pegar texto no necesita esto

### 4.2 — Optimización por el agente (tools + prompt)
- [ ] `src/agent/tools/linkedin.py`:
  - `load_linkedin_profile()` — snapshot actual + inventario de recomendaciones + `target_keywords()`
    + resumen del perfil `.md` para comparar (el "cargar todo para decidir", análogo a
    `load_application`)
  - `save_linkedin_snapshot(content_md)` — guarda lo que Miguel pega/importa
  - `save_linkedin_recommendation(section, content_md)` — escribe `recommendations/<section>.md`
  - `read_linkedin_file(relpath)` — leer cualquier doc
- [ ] Registro en `tools/definitions.py` + `tools/router.py` (el agente central no cambia)
- [ ] Prompt: nueva sección "LinkedIn optimization discipline" en `prompts.py` — flujo:
  - si no hay snapshot o está viejo → pedirle a Miguel que pegue sus secciones (o importe el export)
    y guardarlo con `save_linkedin_snapshot`
  - cargar perfil `.md` (fuente de verdad) + snapshot + `target_keywords`
  - detectar brechas: contenido del `.md` no reflejado en LinkedIn, keywords muy pedidas que faltan,
    puntos débiles (titular genérico, "Acerca de" sin métricas/historia, experiencia sin logros
    cuantificados)
  - generar recomendaciones por sección en voz de LinkedIn (primera persona, atractivo, buscable por
    reclutadores) y guardarlas con `save_linkedin_recommendation`
  - **honestidad estricta**: nunca inventar experiencia/skills que no estén en el perfil `.md`
    (misma regla que la generación de CV)
  - decirle a Miguel exactamente qué copiar/pegar en cada sección de LinkedIn

### 4.3 — Estrategia de contenido y publicaciones (en alcance)
- [ ] `src/agent/tools/linkedin.py`: `save_linkedin_post(slug, content_md)` + `list_linkedin_posts()`
  (escriben/listan en `data/linkedin/posts/`)
- [ ] Prompt: sección "LinkedIn content & posting discipline" en `prompts.py` con los principios de
  un post de alto impacto (gancho en la 1ª línea, estructura narrativa, autenticidad profesional,
  resonancia emocional, CTA). **Nota arquitectónica:** el `JobAgent` standalone no puede invocar la
  skill de Claude Code `linkedin-post-writer`, así que esos principios se **incrustan** en el prompt
  (esa skill queda como la fuente/referencia de los principios, no como dependencia en runtime)
- [ ] Flujo: partir de material real (proyecto terminado, curso, logro, hito de postulación) +
  perfil + mercado objetivo → borrador → guardar en `data/linkedin/posts/<slug>.md` → Miguel revisa
  y publica. Honestidad estricta: el post solo afirma cosas presentes en el perfil `.md` / lo que
  Miguel reporta
- [ ] Integración con el engagement proactivo (Fase 1): lo que Miguel comparte al inicio de sesión
  (nuevas tareas, cursos, logros) es la materia prima para que el agente le sugiera posts

### 4.4 — (opcional) Vista web
- [ ] (opcional) Vista `/linkedin` en el FastAPI existente: snapshot + recomendaciones + posts
  renderizados como markdown, reusando `doc.html` y el renderer ya montados en Fase 3

### Integraciones con los demás componentes
| Desde | Hacia | Mecanismo |
|---|---|---|
| Perfil `.md` (Fase 1) | LinkedIn | fuente de verdad; las recomendaciones derivan de él, nunca inventan |
| Discovery (Fase 2) | LinkedIn | `target_keywords()` agrega skills/keywords más pedidos de las ofertas objetivo (token-free) |
| Applications (Fase 3) | LinkedIn | antes de entrevistas, reforzar el perfil porque las empresas lo van a mirar |
| Engagement proactivo (Fase 1) | LinkedIn posts | lo que Miguel reporta al inicio de sesión alimenta borradores de publicaciones |
| LinkedIn | Agente | tools en `src/agent/tools/linkedin.py` leen `data/linkedin/` + el store de discovery |

### Orden de implementación sugerido
1. `data/linkedin/` + gitignore + `service.py` (snapshot/recs read/write) — test: pegar y releer un snapshot
2. `keywords.py` sobre las ofertas reales de discovery — test: ranking de keywords del mercado
3. Agent tools (`tools/linkedin.py`) + registro — test vía `dispatch()`
4. Prompt "LinkedIn optimization discipline" — test end-to-end: pegar perfil → recomendaciones guardadas
5. Estrategia de posts: `save_linkedin_post`/`list_linkedin_posts` + prompt "content & posting" — test: generar y guardar un borrador
6. (opcional) parser del export ZIP, vista web `/linkedin`

---

## Decisiones de Arquitectura

| Decisión | Elección | Razón |
|---|---|---|
| Formato CV | HTML standalone (base64) | WeasyPrint tuvo layout roto; Claude Design template da mejor resultado |
| Persistencia de ofertas | SQLite stdlib | Dedup por hash, queries, sin servidor extra |
| IA en discovery | Tool-use forzado, 1 llamada/oferta | Minimiza tokens; extrae campos y score en un solo turno |
| Modelo discovery | `claude-haiku-4-5` | Tarea acotada, volumen alto → barato |
| Web UI | FastAPI + Jinja2 + htmx | Un solo proceso, mínimo JS, server-side rendering |
| Playwright | Sí, como fallback | Muchas páginas de ofertas requieren JS para renderizar |
| Discovery ↔ Agente | SQLite como punto de encuentro | Discovery es pipeline determinista; el agente lo consume en fases posteriores |
| Persistencia de postulaciones | Tabla `applications` en el mismo `discovery.db` | Un solo archivo/servidor; tablas disjuntas mantienen los módulos desacoplados |
| Tracking vs status de discovery | `stage` detallado aparte del `status` de triage | Distinta granularidad: triage de oferta vs pipeline de proceso de contratación |
| Interview prep | Markdown en `applications/<slug>/prep/` + tools de agente | El prep es generativo y conversacional; reusa el agente existente, no un módulo aislado |
| Estrategia de entrevista | Reusa `pros`/`cons`/`rationale` de discovery | El breakdown de compatibilidad ya identifica fortalezas y brechas a posicionar |
| Lectura de LinkedIn | Pegar texto / export oficial, sin scraping | ToS prohíbe scraping y banean cuentas; optimizar es periódico, no en tiempo real |
| Optimización LinkedIn | Markdown en `data/linkedin/` + tools de agente | Generativo y conversacional; reusa el agente, como el interview prep |
| Keywords objetivo | Agregación determinista de `offers` de discovery | Datos reales del mercado, token-free; el agente prioriza sobre esa base |
