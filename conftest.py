import pathlib

# Ensures config/.env exists with safe test values before any project module is
# imported. Does NOT overwrite an existing file so real local credentials are kept.
_env_path = pathlib.Path("config/.env")
if not _env_path.exists():
    _env_path.parent.mkdir(exist_ok=True)
    _env_path.write_text(
        "ENV_STATE=LOCAL\n"
        "LOCAL_AMIXTLI_API_REPORTS=http://localhost:8000/api/reports\n"
        'LOCAL_ALLOWED_EMAILS=["admin@test.com"]\n'
        "LOCAL_SECRET_KEY=test-secret-key-for-unit-tests-only\n"
        "LOCAL_SUPABASE_URL=https://dummy-test.supabase.co\n"
        "LOCAL_SUPABASE_KEY=dummy-supabase-key-for-tests-only\n"
        "LOCAL_SUPABASE_URL_API=https://dummy-test.supabase.co/rest/v1/reports\n"
    )
