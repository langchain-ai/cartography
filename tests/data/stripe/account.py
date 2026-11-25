STRIPE_ACCOUNT_ID = "acct_1Nv0FGQ9RKHgCVdK"

STRIPE_ACCOUNT = {
    "id": STRIPE_ACCOUNT_ID,
    "object": "account",
    "business_profile": {
        "mcc": "5734",
        "name": "Springfield Nuclear Power Plant",
        "support_email": "support@snpp.example.com",
        "url": "https://snpp.example.com",
    },
    "business_type": "company",
    "capabilities": {
        "card_payments": "active",
        "transfers": "active",
        "us_bank_account_ach_payments": "inactive",
    },
    "charges_enabled": True,
    "controller": {"type": "account"},
    "country": "US",
    "created": 1695830751,
    "default_currency": "usd",
    "details_submitted": True,
    "email": "billing@snpp.example.com",
    "company": {"tax_id_provided": True},
    "external_accounts": {"object": "list", "data": []},
    "metadata": {"internal": "do-not-ingest"},
    "payouts_enabled": True,
    "requirements": {"disabled_reason": None, "currently_due": []},
    "settings": {
        "card_payments": {
            "decline_on": {"avs_failure": False, "cvc_failure": True},
        },
        "dashboard": {"display_name": "SNPP", "timezone": "America/Los_Angeles"},
    },
    "tos_acceptance": {"date": 1695830751, "ip": "203.0.113.10"},
    "type": "standard",
}
