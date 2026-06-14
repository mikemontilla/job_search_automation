# Job Search Automation

A project to automate and optimize the key steps involved in finding a job in a target area. The goal is to reduce manual effort, increase consistency, and improve the quality of each application.

> See [ROADMAP.md](ROADMAP.md) for the full development plan and phase status.

---

## Usage

### Prerequisites

All commands assume the `job_search` conda environment:

```bash
conda activate job_search
# or use the full path:
# /home/miguel/anaconda3/envs/job_search/bin/python
```

Copy `.env.example` to `.env` and set your Anthropic API key:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

---

### 1. CV Agent — conversational profile & resume manager

```bash
python -m src.agent
```

The agent greets you, asks proactive questions about your week, and can:
- Update your professional profile in EN / ES / FR simultaneously.
- Generate a tailored CV (HTML) for a specific job offer.

Generated CVs are saved to `applications/<job-slug>/<language>/cv.html` — open directly in a browser and print to PDF.

---

### 2. Job Discovery System — find and score job offers

#### Start the web UI

```bash
python -m src.discovery web
```

Open **http://127.0.0.1:8000** in a browser. From here you can:

- **Add a job offer** — paste any public job-offer URL in the input at the top and click *Add offer*. The system fetches the page, extracts the structured fields, and scores the match against your profile. The new offer appears in the list in a few seconds.
- **Review offers** — browse the table sorted by compatibility score. Click a title to see the full detail: responsibilities, required skills, contract type, compatibility breakdown by dimension, and the AI rationale.
- **Triage** — for each offer, use the inline buttons to:
  - 📝 Mark as **applying** (you started an application process).
  - 👁 Mark as **reviewed** (read but no action yet).
  - ↗ Open the **original job posting** in a new tab.
  - 🗑 **Delete** (soft delete — the offer won't be re-ingested on the next run).
- **Filter** — by status, recommended-only, or sort by score / date.
- **Run search** — click *Run search now* to trigger the pipeline over all configured automatic sources.

#### Add a single offer from the terminal

```bash
python -m src.discovery ingest "https://careers.example.com/jobs/embedded-engineer-123"
```

#### Run the full discovery pipeline

```bash
python -m src.discovery run
```

Runs all sources configured in `config/discovery_config.yaml`. In Phase 2.0 this is a no-op unless you have manual sources — use `ingest` or the web UI instead. Automatic sources (career pages, email alerts) are added in later phases.

#### Schedule automatic runs with cron

```bash
# Example: run every day at 8:00 AM
0 8 * * * cd /home/miguel/Documents/dev_projects/job_search_automation && \
  /home/miguel/anaconda3/envs/job_search/bin/python -m src.discovery run >> data/discovery.log 2>&1
```

---

## Features

### 1. Job Offer Discovery

Automated search for job postings across desired companies using scraping, APIs, or similar data extraction methods. Sources include company career pages, LinkedIn, Indeed, and others (to be defined over time).

### 2. Job Offer Filtering

Intelligent filtering of discovered job offers to identify the ones that best match the applicant's profile and maximize the probability of landing the position.

### 3. LinkedIn Profile Optimization

Continuous updates and improvements to the LinkedIn profile to make it as attractive as possible for the targeted job offers.

### 4. Resume Management

- Creation of a resume in a code-friendly format (LaTeX, HTML/CSS/JS, or another language suitable for programmatic graphic manipulation by an AI).
- Continuous updates with new experiences, courses, certifications, etc.
- Generation of tailored resume versions optimized for specific job postings.

### 5. Application Data Files

Markdown files containing the data used for applications across different companies. These can vary depending on the specific job offer.

### 6. Interview Preparation

Stored preparation files that include:

- Best answers for initial contact/screening calls.
- Preparation material for technical interviews.

### 7. Application Tracking and Follow-Up

#### 7.1 Tracking Dashboard

A spreadsheet or HTML view backed by a database to visualize:

- Discovered job offers.
- Active application processes.
- Resume version used for each application.
- Contact responsible for the next interview.
- Relevant company information for the interview.
- Current stage in the hiring pipeline.
- List of relevant files for each application.

#### 7.2 Application Folders

Each application gets its own folder containing all relevant files:

- Resume version used.
- Interview preparation documents.
- Any other supporting materials.
