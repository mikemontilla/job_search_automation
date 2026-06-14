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
