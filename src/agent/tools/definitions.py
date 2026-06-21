TOOLS = [
    {
        "name": "read_profile",
        "description": (
            "Read the professional profile in the specified language. "
            "If section_key is provided, returns only that section. "
            "If omitted, returns the full profile."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["en", "es", "fr"],
                    "description": "Profile language to read.",
                },
                "section_key": {
                    "type": "string",
                    "enum": [
                        "summary", "experience", "education", "publications",
                        "skills", "languages", "interests", "projects", "hobbies",
                    ],
                    "description": "Canonical section key to read. Omit to read the full profile.",
                },
            },
            "required": ["language"],
        },
    },
    {
        "name": "update_profile_section",
        "description": (
            "Replace the content of one section in one language profile file. "
            "Always call this 3 times (once per language: en, es, fr) when updating a section. "
            "Generate all 3 translations yourself before calling this tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["en", "es", "fr"],
                    "description": "Language of the profile file to update.",
                },
                "section_key": {
                    "type": "string",
                    "enum": [
                        "summary", "experience", "education", "publications",
                        "skills", "languages", "interests", "projects", "hobbies",
                    ],
                    "description": "Canonical section key to update.",
                },
                "new_content": {
                    "type": "string",
                    "description": (
                        "Full new markdown content for the section, including the ## heading. "
                        "Must be written in the target language."
                    ),
                },
            },
            "required": ["language", "section_key", "new_content"],
        },
    },
    {
        "name": "list_job_offers",
        "description": "List all job offers stored in the applications/ and application_data/ folders.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "load_job_description",
        "description": "Read the job description file for a specific job offer by its folder name or index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Folder name or numeric index (from list_job_offers) of the job offer.",
                },
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "generate_cv_json",
        "description": (
            "Generate a tailored profile.json for the CV template and copy the template files "
            "to applications/<job_slug>/<language>/. The user then opens 'CV Template.dc.html' "
            "in a browser and prints to PDF (Legal size, no margins). "
            "Call once per language needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["en", "es", "fr"],
                    "description": "Language of the CV to generate.",
                },
                "job_slug": {
                    "type": "string",
                    "description": "Short identifier for the job (e.g. 'accenture-embedded-2026'). Used for the output folder name.",
                },
                "cv_data": {
                    "type": "object",
                    "description": (
                        "Structured CV content matching profile.json format: "
                        "name, title, subtitle, photo, phone, location, email, linkedin, github, summary, "
                        "skills (list of {name, level, pct}), tools (list of strings), "
                        "languages (list of {name, level, pct}), "
                        "interests (list of {label, icon} — icon: camera|piano|chess|dumbbell), "
                        "experience (list of {role, company, place, dates, note, bullets, stack}), "
                        "education (list of {degree, school, place, dates, note}), "
                        "publications (list of {title, meta}), "
                        "references (list of {name, role, phone})."
                    ),
                },
            },
            "required": ["language", "job_slug", "cv_data"],
        },
    },
    {
        "name": "list_discovered_offers",
        "description": (
            "List job offers found by the automated discovery pipeline (career-page "
            "scrapers and email alerts), already scored for compatibility with the "
            "profile. Use this to find offers to build a CV for or prep an interview from."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["new", "reviewed", "applying", "discarded"],
                    "description": "Filter by triage status. Omit to get all non-discarded offers.",
                },
                "recommended_only": {
                    "type": "boolean",
                    "description": "If true, only return offers whose score met the configured threshold.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max offers to return, sorted by score descending. Defaults to 20.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "load_discovered_offer",
        "description": (
            "Load full details of one discovered offer by its id (from list_discovered_offers): "
            "structured fields, the AI compatibility breakdown/rationale/pros/cons, and the raw "
            "job description text — enough to generate a tailored CV or prep an interview."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "offer_id": {
                    "type": "string",
                    "description": "The offer's id, as returned by list_discovered_offers.",
                },
            },
            "required": ["offer_id"],
        },
    },
    {
        "name": "run_job_search",
        "description": (
            "Trigger the discovery pipeline immediately over all configured sources "
            "(career pages, Serma-style JSON endpoints, email alerts) instead of waiting "
            "for the next scheduled run. Use when the user asks to check for new offers now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_applications",
        "description": (
            "List tracked applications (postulaciones), optionally filtered by pipeline stage. "
            "Use this to see what's in progress, or to find an application id to load."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": [
                        "interested", "applied", "screening", "technical", "final",
                        "offer", "accepted", "rejected", "withdrawn",
                    ],
                    "description": "Filter by pipeline stage. Omit to get all applications.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "load_application",
        "description": (
            "Load everything needed to prep an interview or plan strategy for one application: "
            "metadata, the job description, an inventory of generated files (CVs, prep docs, "
            "research), the event timeline, and — if it came from discovery — the compatibility "
            "score/pros/cons/rationale of the original offer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The application's id (slug), as returned by list_applications.",
                },
            },
            "required": ["app_id"],
        },
    },
    {
        "name": "read_application_file",
        "description": (
            "Read the raw content of any generated file inside an application's folder "
            "(e.g. 'prep/technical.md', 'research/company.md', 'en/profile.json')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The application's id (slug).",
                },
                "relpath": {
                    "type": "string",
                    "description": "Path relative to applications/<app_id>/, e.g. 'prep/screening.md'.",
                },
            },
            "required": ["app_id", "relpath"],
        },
    },
    {
        "name": "save_prep_document",
        "description": (
            "Write an interview-prep document for an application to prep/<kind>.md "
            "(e.g. kind='screening', 'technical', 'questions_for_them', 'strategy') "
            "and log a document_added event."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The application's id (slug).",
                },
                "kind": {
                    "type": "string",
                    "description": "Doc name without extension, e.g. 'screening', 'technical', 'questions_for_them', 'strategy'.",
                },
                "content_md": {
                    "type": "string",
                    "description": "Full markdown content of the document.",
                },
            },
            "required": ["app_id", "kind", "content_md"],
        },
    },
    {
        "name": "save_interviewer_research",
        "description": (
            "Write research about a specific interviewer to research/interviewer_<slug>.md "
            "(their role, trajectory, possible common ground or technical interests) and log "
            "a document_added event. Use before drafting technical.md / questions_for_them.md "
            "once interviewer names/roles are known (from an interview_scheduled event)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The application's id (slug).",
                },
                "slug": {
                    "type": "string",
                    "description": "Short identifier for the interviewer, e.g. 'jane-doe'.",
                },
                "content_md": {
                    "type": "string",
                    "description": "Full markdown content of the research notes.",
                },
            },
            "required": ["app_id", "slug", "content_md"],
        },
    },
    {
        "name": "update_application",
        "description": (
            "Update tracked metadata for an application: pipeline stage, HR contact, notes, "
            "or the next action and its date. Omit fields that shouldn't change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The application's id (slug).",
                },
                "stage": {
                    "type": "string",
                    "enum": [
                        "interested", "applied", "screening", "technical", "final",
                        "offer", "accepted", "rejected", "withdrawn",
                    ],
                },
                "hr_contact": {
                    "type": "object",
                    "description": "Contact info, e.g. {name, email, phone, role}.",
                },
                "notes": {"type": "string"},
                "next_action": {"type": "string"},
                "next_action_date": {"type": "string", "description": "ISO date, e.g. 2026-07-01."},
            },
            "required": ["app_id"],
        },
    },
    {
        "name": "log_application_event",
        "description": (
            "Add an event to an application's timeline: a note, an interview being scheduled "
            "(detail can list participants as JSON: [{name, role, linkedin_url}]), an interview "
            "completed, or a document being added."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The application's id (slug).",
                },
                "event_type": {
                    "type": "string",
                    "enum": ["stage_change", "note", "interview_scheduled", "interview_done", "document_added"],
                },
                "title": {"type": "string"},
                "detail": {"type": "string", "description": "Free text, or a JSON string for structured data like interviewer lists."},
                "event_date": {"type": "string", "description": "ISO date, e.g. 2026-07-01."},
            },
            "required": ["app_id", "event_type"],
        },
    },
    {
        "name": "save_session_note",
        "description": (
            "Persist a short summary of what was updated or created in this session. "
            "Call this at the end of any session where changes were made."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "Brief summary of session changes (max 200 characters).",
                },
            },
            "required": ["note"],
        },
    },
]
