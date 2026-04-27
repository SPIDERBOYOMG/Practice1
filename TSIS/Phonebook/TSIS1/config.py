try:
    from secrets import DB_CONFIG
except (ImportError, ModuleNotFoundError):
    DB_CONFIG = {
        "host":     "localhost",
        "port":     5433,
        "dbname":   "Laba",
        "user":     "postgres",
        "password": "postgres",
    }
