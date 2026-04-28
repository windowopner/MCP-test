from typing import Any, Callable

from app.services.google import classroom, docs, drive, slides

# ── Callable registry used by executor ───────────────────────────────────────

TOOL_REGISTRY: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    # Drive
    "list_files":    lambda i: drive.list_files(i.get("query", ""), int(i.get("max_results", 20))),
    "create_folder": lambda i: drive.create_folder(i["name"], i.get("parent_id")),
    "upload_file":   lambda i: drive.upload_file(i["name"], i["content"], i.get("mime_type", "text/plain"), i.get("parent_id")),
    # Docs
    "create_doc":         lambda i: docs.create_doc(i["title"], i.get("content", "")),
    "append_text":        lambda i: docs.append_text(i["document_id"], i["text"]),
    "create_outline_doc": lambda i: docs.create_outline_doc(i["title"], i.get("sections", [])),
    # Slides
    "create_deck":            lambda i: slides.create_deck(i["title"]),
    "add_slide":              lambda i: slides.add_slide(i["presentation_id"], i.get("layout", "BLANK")),
    "generate_from_outline":  lambda i: slides.generate_from_outline(i["title"], i.get("slides", [])),
    # Classroom
    "list_courses":           lambda i: classroom.list_courses(int(i.get("page_size", 20))),
    "list_assignments":       lambda i: classroom.list_assignments(i["course_id"], int(i.get("page_size", 20))),
    "get_assignment_details": lambda i: classroom.get_assignment_details(i["course_id"], i["assignment_id"]),
}

# ── MCP tool definitions (JSON Schema) used by tools/list ────────────────────

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "list_files",
        "description": "List files and folders in Google Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Drive API query string (e.g. \"name contains 'report'\"). Defaults to all non-trashed files.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of files to return.",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "create_folder",
        "description": "Create a new folder in Google Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Folder name."},
                "parent_id": {"type": "string", "description": "ID of the parent folder (optional)."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "upload_file",
        "description": "Upload a text file to Google Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "File name including extension."},
                "content": {"type": "string", "description": "Text content of the file."},
                "mime_type": {
                    "type": "string",
                    "description": "MIME type of the file.",
                    "default": "text/plain",
                },
                "parent_id": {"type": "string", "description": "ID of the parent folder (optional)."},
            },
            "required": ["name", "content"],
        },
    },
    {
        "name": "create_doc",
        "description": "Create a new Google Docs document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title."},
                "content": {"type": "string", "description": "Initial text content (optional)."},
            },
            "required": ["title"],
        },
    },
    {
        "name": "append_text",
        "description": "Append text to an existing Google Docs document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "The Google Docs document ID."},
                "text": {"type": "string", "description": "Text to append."},
            },
            "required": ["document_id", "text"],
        },
    },
    {
        "name": "create_outline_doc",
        "description": "Create a Google Docs document structured from a list of sections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title."},
                "sections": {
                    "type": "array",
                    "description": "List of sections, each with optional 'heading' and 'body' strings.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heading": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "create_deck",
        "description": "Create a new empty Google Slides presentation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Presentation title."},
            },
            "required": ["title"],
        },
    },
    {
        "name": "add_slide",
        "description": "Add a new slide to an existing Google Slides presentation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "presentation_id": {"type": "string", "description": "The presentation ID."},
                "layout": {
                    "type": "string",
                    "description": "Slide layout (e.g. BLANK, TITLE, TITLE_AND_BODY).",
                    "default": "BLANK",
                },
            },
            "required": ["presentation_id"],
        },
    },
    {
        "name": "generate_from_outline",
        "description": "Generate a Google Slides presentation from a structured outline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Presentation title."},
                "slides": {
                    "type": "array",
                    "description": "List of slide objects. Each can be type 'title' (with 'title' and 'subtitle') or 'body' (with 'title' and 'bullets' list).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["title", "body"]},
                            "title": {"type": "string"},
                            "subtitle": {"type": "string"},
                            "bullets": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_courses",
        "description": "List Google Classroom courses the authenticated user is enrolled in or teaches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_size": {
                    "type": "integer",
                    "description": "Maximum number of courses to return.",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "list_assignments",
        "description": "List assignments (coursework) for a specific Google Classroom course.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "course_id": {"type": "string", "description": "The Classroom course ID."},
                "page_size": {
                    "type": "integer",
                    "description": "Maximum number of assignments to return.",
                    "default": 20,
                },
            },
            "required": ["course_id"],
        },
    },
    {
        "name": "get_assignment_details",
        "description": "Get full details for a specific assignment in a Google Classroom course.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "course_id": {"type": "string", "description": "The Classroom course ID."},
                "assignment_id": {"type": "string", "description": "The assignment (courseWork) ID."},
            },
            "required": ["course_id", "assignment_id"],
        },
    },
]
