def _e(cat, name, path, desc):
    return {"name": name, "method": "GET", "path": path, "category": cat,
            "description": desc, "requires_id": "{" in path}

ENDPOINTS = [
    _e("Users", "Current User", "/v1/users/me", "Authenticated user"),
    _e("Users", "List Users", "/v1/users", "Users visible to you"),
    _e("Users", "User", "/v1/users/{id}", "A user by ID"),
    _e("Users", "User Sections", "/v1/users/{id}/sections", "Sections a user is in"),
    _e("Users", "User Groups", "/v1/users/{id}/groups", "Groups a user is in"),
    _e("Users", "User Grades", "/v1/users/{id}/grades", "Grades for a user"),
    _e("Users", "User Events", "/v1/users/{id}/events", "Events for a user"),
    _e("Users", "User Updates", "/v1/users/{id}/updates", "Updates by a user"),
    _e("Users", "User Documents", "/v1/users/{id}/documents", "Documents of a user"),
    _e("Schools", "List Schools", "/v1/schools", "Schools"),
    _e("Schools", "School", "/v1/schools/{id}", "A school by ID"),
    _e("Districts", "List Districts", "/v1/districts", "Districts"),
    _e("Courses", "List Courses", "/v1/courses", "Courses"),
    _e("Courses", "Course", "/v1/courses/{id}", "A course by ID"),
    _e("Sections", "List Sections", "/v1/sections", "Sections (may be empty)"),
    _e("Sections", "Section", "/v1/sections/{id}", "A section by ID"),
    _e("Groups", "List Groups", "/v1/groups", "Groups"),
    _e("Groups", "Group", "/v1/groups/{id}", "A group by ID"),
    _e("Assignments", "Section Assignments", "/v1/sections/{id}/assignments", "Assignments in a section"),
    _e("Documents", "Section Documents", "/v1/sections/{id}/documents", "Documents in a section"),
    _e("Events", "Section Events", "/v1/sections/{id}/events", "Events in a section"),
    _e("Messages", "Inbox", "/v1/messages/inbox", "Inbox messages"),
    _e("Messages", "Sent", "/v1/messages/sent", "Sent messages"),
    _e("Grades", "Section Grades", "/v1/sections/{id}/grades", "Grades in a section"),
    _e("Discussions", "Section Discussions", "/v1/sections/{id}/discussions", "Discussions in a section"),
    _e("Pages", "Section Pages", "/v1/sections/{id}/pages", "Pages in a section"),
    _e("Roles", "List Roles", "/v1/roles", "Roles"),
]
# Permissions and Search are left out: add entries here once verified against the docs.
CATEGORIES = sorted({e["category"] for e in ENDPOINTS})
