"""
Django settings for poetry_project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import environ
import os  # Added for BASE_DIR usage in logging

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)  # Set default DEBUG to False
)

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
environ.Env.read_env(env_file=BASE_DIR / '.env')

# Charset settings
FILE_CHARSET = 'utf-8'
DEFAULT_CHARSET = 'utf-8'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Define allowed hosts from environment variable, split by commas
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'poetry_app',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'markdownx',
    'django_summernote',
    'django.contrib.humanize',
    'channels',
    'django_ckeditor_5',
    'reversion',
    'widget_tweaks',
    'storages',
]

# Security settings for HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# ASGI application for Channels
ASGI_APPLICATION = 'poetry_project.asgi.application'

# Channel layers configuration using Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                {
                    'address': (env('REDIS_HOST', default='127.0.0.1'), env.int('REDIS_PORT', default=6379)),
                    'password': env('REDIS_PASSWORD', default=None),
                },
            ],
        },
    },
}

# Crispy Forms configuration
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'poetry_app.middleware.UpdateUserStreakMiddleware',
]

# URL configuration
ROOT_URLCONF = 'poetry_project.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # global templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'poetry_app.context_processors.current_year',
                'poetry_app.context_processors.notifications_enabled',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'poetry_project.wsgi.application'

# Database configuration using environment variable
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# API Keys from environment variables
YOUTUBE_API_KEY = env('YOUTUBE_API_KEY')
PEXELS_API_KEY = env('PEXELS_API_KEY')

# Feature flags
NOTIFICATIONS_ENABLED = False

# Static files (CSS, JavaScript, Images) configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    #BASE_DIR / 'poetry_app' / 'static',
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication redirects
LOGOUT_REDIRECT_URL = 'login'
LOGIN_REDIRECT_URL = 'poetry_app:discover'

# Summernote Configuration
SUMMERNOTE_CONFIG = {
    'toolbar': [
        ['style', ['bold', 'italic', 'underline']],
        ['para', ['paragraph']],
    ],
    'height': 500,
    'width': '100%',
    'css': (
        '/static/css/summernote.css',
    ),
}

# CKEditor Configuration
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {  # Console handler replaces file handler
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {  # Root logger uses only console handler
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {  # Django logger uses only console handler
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {  # Channels logger uses only console handler
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'poetry_app': {  # console handler
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}