from typing import Any

from googleapiclient.discovery import build

from app.services.google.auth import get_credentials


def _svc():
    return build("classroom", "v1", credentials=get_credentials())


def list_courses(page_size: int = 20) -> dict[str, Any]:
    result = _svc().courses().list(pageSize=page_size).execute()
    courses = result.get("courses", [])
    return {
        "courses": [
            {
                "id": c["id"],
                "name": c.get("name"),
                "section": c.get("section"),
                "state": c.get("courseState"),
                "url": c.get("alternateLink"),
            }
            for c in courses
        ],
        "count": len(courses),
    }


def list_assignments(course_id: str, page_size: int = 20) -> dict[str, Any]:
    result = _svc().courses().courseWork().list(courseId=course_id, pageSize=page_size).execute()
    items = result.get("courseWork", [])
    return {
        "course_id": course_id,
        "assignments": [
            {
                "id": w["id"],
                "title": w.get("title"),
                "description": w.get("description"),
                "state": w.get("state"),
                "due_date": w.get("dueDate"),
                "max_points": w.get("maxPoints"),
                "url": w.get("alternateLink"),
            }
            for w in items
        ],
        "count": len(items),
    }


def get_assignment_details(course_id: str, assignment_id: str) -> dict[str, Any]:
    w = _svc().courses().courseWork().get(courseId=course_id, id=assignment_id).execute()
    return {
        "id": w["id"],
        "course_id": course_id,
        "title": w.get("title"),
        "description": w.get("description"),
        "state": w.get("state"),
        "due_date": w.get("dueDate"),
        "due_time": w.get("dueTime"),
        "max_points": w.get("maxPoints"),
        "work_type": w.get("workType"),
        "materials": w.get("materials", []),
        "url": w.get("alternateLink"),
    }
