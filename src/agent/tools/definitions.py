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
        "name": "generate_cv_pdf",
        "description": (
            "Render the HTML/CSS Jinja2 CV template with the provided data and compile it to PDF. "
            "Call this once per language needed. The PDF is saved in applications/<job_slug>/."
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
                        "Structured CV content tailored for the job offer. "
                        "Keys: name, title, location, email, linkedin, github, summary, "
                        "experience (list of {company, role, period, location, bullets, stack}), "
                        "education (list of {institution, degree, period, details}), "
                        "publications (list of strings), "
                        "skills (object with programming, frameworks, devops, areas), "
                        "languages (list of {language, level, certification}), "
                        "interests (list of strings), projects (list of strings), hobbies (string)."
                    ),
                },
                "accent_color": {
                    "type": "string",
                    "description": "CSS hex color for section headings (e.g. '#2563eb'). Optional, defaults to dark blue.",
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
