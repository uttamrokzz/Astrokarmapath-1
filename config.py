# -*- coding: utf-8 -*-
import os

URL = os.environ.get('TURSO_DATABASE_URL',
    'libsql://astrokarmapath-astrokarmapath.aws-ap-south-1.turso.io')
TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

try:
    from local_config import TOKEN as _LOCAL
    if _LOCAL:
        TOKEN = _LOCAL
except ImportError:
    pass
