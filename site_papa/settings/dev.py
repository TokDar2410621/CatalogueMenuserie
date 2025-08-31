from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-6g(ie^31l=idy19ay!66sq#9*q#1c_jjbk-*pql5(*l=8homao"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["https://fkbois.onrender.com/", "localhost", "127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


