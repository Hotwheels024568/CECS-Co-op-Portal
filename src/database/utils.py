def get_constraint_name_from_integrity_error(e) -> str:
    # Handles asyncpg, psycopg2, or most DBAPIs used with SQLAlchemy
    try:
        return getattr(getattr(e.orig, "diag", None), "constraint_name", "") or str(e)
    except Exception:
        return str(e)
