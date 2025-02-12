import environ
from decouple import config
from .settings import *

# Initialize environ
env = environ.Env()

# Set debug
DEBUG = True

# Override database settings for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Override AWS settings for local development
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='poetryappbucket')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-2')

# Use local file storage instead of S3 for development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Allow all hosts in development
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Disable Redis/Channels in development
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Disable forced HTTPS in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False