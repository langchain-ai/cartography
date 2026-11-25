from typing import Any

BASETEN_ENVIRONMENT_GROUPS_BY_TEAM: dict[str, dict[str, Any]] = {
    "team_default01": {
        "items": [
            {
                "name": "production",
                "team_id": "team_default01",
                "team_name": "Default",
                "manage_access": {
                    "is_restricted": True,
                    "users": [
                        {
                            "user_id": "user_marge01",
                            "email": "mbsimpson@simpson.corp",
                            "name": "Marge Simpson",
                        },
                    ],
                },
            },
            {
                "name": "staging",
                "team_id": "team_default01",
                "team_name": "Default",
                "manage_access": {"is_restricted": False, "users": []},
            },
        ],
        "pagination": {"has_more": False, "cursor": None},
    },
    "team_research01": {
        "items": [],
        "pagination": {"has_more": False, "cursor": None},
    },
}
