STRIPE_APP_INSTALLS = [
    {
        "id": "appinst_61VGZmT4pXc8Rk2w41LUZiLcTVChK7Ab",
        "object": "apps.install",
        "account": "acct_1Nv0FGQ9RKHgCVdK",
        "app": "app_61VGZkQ7mRbN3xPa41LUZiLcTVChQ9Ye",
        "approval_required": True,
        "auth_code": "ac_do_not_store",
        "channel": "public",
        "content_security_policy_granted": {
            "connect_src": ["https://api.example.com/"],
            "image_src": ["https://cdn.example.com/"],
        },
        "content_security_policy_pending": {"connect_src": [], "image_src": []},
        "created": 1725000000,
        "created_by": None,
        "endpoints_granted": ["https://example.com/stripe/webhook"],
        "endpoints_pending": [],
        "livemode": True,
        "permissions_granted": ["customer_read", "event_read"],
        "permissions_pending": ["payment_intent_write"],
        "status": "installed",
    },
]
