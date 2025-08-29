from .base import *

DEBUG = False
CSRF_TRUSTED_ORIGINS = ["https://fkbois.onrender.com"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
try:
    from .local import *
except ImportError:
    pass
