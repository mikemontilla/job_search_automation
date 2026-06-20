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
        │     └─ DiscoveryTools (tools/discovery_tools.py)      [Phase 2.3 ⬜]
        └─ prompts.py

src/discovery/  ←→  FastAPI web UI + SQLite store               [Phase 2 🔄]
src/tracking/                                                    [Phase 3 ⬜]
src/linkedin/                                                    [Phase 4 ⬜]
```

**Regla de escalabilidad:** cada módulo nuevo agrega archivos en `src/`. Si necesita
exponerse al agente conversacional, registra herramientas en `tools/definitions.py` +
`tools/router.py`. El agente central no cambia.

**Punto de encuentro entre módulos:** `data/discovery.db` (SQLite).
El pipeline de descubrimiento escribe ahí; el agente conversacional lo lee.

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

### Fase 2.3 — Integración con el agente ⬜ PENDIENTE

Herramientas de solo-lectura para el agente conversacional:
- `list_discovered_offers` — lista ofertas del store con filtros
- `load_discovered_offer` — carga detalle → generar CV / preparar entrevista
- `run_job_search` (opcional) — dispara el pipeline desde el chat

Registro en `tools/definitions.py` + `tools/router.py`. El agente central no cambia.

---

## Phase 3 — Application Tracking ⬜ PENDIENTE

Dashboard web de seguimiento de postulaciones (integrado en el servidor FastAPI de Phase 2):
- Estado del proceso (screening, entrevista técnica, oferta, rechazado)
- Versión del CV usado, contacto de RRHH, archivos relevantes
- Archivos futuros: `src/tracking/`

---

## Phase 4 — LinkedIn Optimization ⬜ PENDIENTE

- Sincronizar perfil LinkedIn con los archivos .md (fuente de verdad)
- Optimizar para las ofertas objetivo
- Archivos futuros: `src/linkedin/`

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
