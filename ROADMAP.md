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

**Prueba en vivo pendiente (usa tokens):**
1. `python -m src.discovery web` → pegar URL real en la UI
2. Verificar score, campos parseados y breakdown en el browser
3. Re-pegar la misma URL → no se duplica, log `skip (already seen, no AI call)`

### Fase 2.1 — Fuentes automáticas: career pages ⬜ PENDIENTE

- `src/discovery/sources/career_page.py`
- Lee URLs preconfiguradas en `discovery_config.yaml → sources[]`
  (cada URL ya tiene los filtros aplicados, ej. `https://careers.airbus.com/...?keyword=embedded`)
- Playwright navega la lista de resultados → extrae URLs individuales → pipeline
- Documentar cron job para ejecución automática

### Fase 2.2 — Alertas por email ⬜ PENDIENTE

- `src/discovery/sources/email_alerts.py`
- Gmail API (OAuth read-only): leer alertas de LinkedIn / Indeed
- Seguir links con contexto Playwright persistente (usuario ya hizo login)
- Configurar en `discovery_config.yaml → email`

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
