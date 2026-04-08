"""
OpenAPI 3.0 configuration for flask-smorest.
These keys are merged into Flask's app.config before Api(app) is called.
"""

OPENAPI_CONFIG = {
    "API_TITLE":            "Financial Pipeline API",
    "API_VERSION":          "v1",
    "OPENAPI_VERSION":      "3.0.3",
    "OPENAPI_URL_PREFIX":   "/",
    "OPENAPI_SWAGGER_UI_PATH": "/docs",
    "OPENAPI_SWAGGER_UI_URL":  "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    "OPENAPI_JSON_PATH":    "api-spec.json",
    "API_SPEC_OPTIONS": {
        "info": {
            "description": (
                "REST API for the Financial Reporting Pipeline. "
                "Run financial analyses, compare assets, schedule email reports, "
                "and manage the report cache. "
                "Rate limits apply to write endpoints — see individual operation descriptions."
            ),
            "contact": {"name": "Finpipe"},
        },
        "tags": [
            {"name": "Assets",     "description": "Asset categories, periods, intervals, and ticker validation"},
            {"name": "Pipeline",   "description": "Run the financial analysis pipeline for a single asset"},
            {"name": "Comparison", "description": "Side-by-side comparison of two assets"},
            {"name": "Schedule",   "description": "Manage scheduled email reports"},
            {"name": "Reports",    "description": "Serve generated charts and PDF reports"},
            {"name": "Cache",      "description": "Inspect and manage the report cache"},
        ],
    },
}
