import os

URL   = os.environ.get("TURSO_DATABASE_URL",
        "libsql://astrokarmapath-astrokarmapath.aws-ap-south-1.turso.io")
TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
