FIREWORKS_ACCOUNT_ID = "springfield-nuclear"

FIREWORKS_ACCOUNT = {
    "name": "accounts/springfield-nuclear",
    "displayName": "Springfield Nuclear Power Plant",
    "createTime": "2025-01-15T18:00:00Z",
    "accountType": "ENTERPRISE",
    "email": "billing@springfield-nuclear.example",
    "state": "READY",
    "status": {"code": "OK", "message": ""},
    "suspendState": "UNSUSPENDED",
    "updateTime": "2026-02-01T09:30:00Z",
    "productivityOnly": False,
}

# ZDR on by default, with training explicitly opted out; deny-all model access with
# one allowed model; US-only residency.
FIREWORKS_POLICY_SETTINGS = {
    "name": "accounts/springfield-nuclear/policySettings",
    "defaultPermissions": {
        "allowServerless": False,
        "allowDedicatedDeployments": False,
        "allowTraining": False,
        "allowServerlessFast": False,
    },
    "rules": [
        {
            "model": "accounts/fireworks/models/qwen3-235b-a22b",
            "permissions": {
                "allowServerless": True,
                "allowDedicatedDeployments": True,
                "allowTraining": False,
                "allowServerlessFast": True,
            },
        },
    ],
    "updateTime": "2026-02-01T09:30:00Z",
    "cmekRequired": True,
    "residency": "US",
    "zeroDataRetention": {
        "defaultEnforced": True,
        "training": {"enforcement": "NOT_ENFORCED"},
    },
}
