"""
Django settings for gaming_leaderboard project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'django_extensions',  # Enhanced Django shell and other tools
    'leaderboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add NewRelic middleware only in production
if not DEBUG:
    try:
        import newrelic.agent
        MIDDLEWARE.insert(0, 'newrelic.agent.django_middleware')
    except ImportError:
        pass

ROOT_URLCONF = 'gaming_leaderboard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gaming_leaderboard.wsgi.application'
ASGI_APPLICATION = 'gaming_leaderboard.asgi.application'

# Database - MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'gaming_leaderboard'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'mysql'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10,
        },
        'CONN_MAX_AGE': 60,  # Keep connections alive for 60 seconds
        'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
    }
}

# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

# Caches
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'gaming_leaderboard',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Timeout configurations (integrated from timeout_settings.py)
WEBSOCKET_SETTINGS = {
    'CONNECT_TIMEOUT': 10,      # Seconds to wait for connection
    'RECEIVE_TIMEOUT': 30,      # Seconds to wait for message receive
    'SEND_TIMEOUT': 10,         # Seconds to wait for message send
    'DISCONNECT_TIMEOUT': 5,    # Seconds to wait for graceful disconnect
    'GROUP_TIMEOUT': 2,         # Seconds to wait for group operations
}

DATABASE_TIMEOUT_SETTINGS = {
    'QUERY_TIMEOUT': 10,        # Seconds for individual queries
    'TRANSACTION_TIMEOUT': 30,  # Seconds for transactions
    'CONNECTION_TIMEOUT': 10,   # Seconds for connection establishment
}

WEBSOCKET_CACHE_SETTINGS = {
    'LEADERBOARD_TTL': 15,      # Seconds to cache leaderboard data
    'USER_RANK_TTL': 30,        # Seconds to cache user rank data
    'GAME_DATA_TTL': 300,       # Seconds to cache game data
}

PERFORMANCE_SETTINGS = {
    'LOG_SLOW_QUERIES': True,          # Log queries taking longer than threshold
    'SLOW_QUERY_THRESHOLD': 5.0,       # Seconds threshold for slow queries
    'LOG_WEBSOCKET_ERRORS': True,      # Log WebSocket connection errors
    'MAX_MESSAGE_SIZE': 1024,          # Max WebSocket message size in bytes
}

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 1500,  # Default 100
            'expiry': 60,      # Default 60 seconds
            'group_expiry': 86400,  # 24 hours
            'symmetric_encryption_keys': [SECRET_KEY],
        },
        'OPTIONS': {
            'connection_pool_kwargs': {
                'max_connections': 20,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
            },
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# New Relic
if not DEBUG:
    try:
        import newrelic.agent
        newrelic.agent.initialize('newrelic.ini')
    except ImportError:
        pass

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'websocket_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'websocket.log',
            'formatter': 'verbose',
        },
        'performance_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'performance.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'leaderboard.consumers': {
            'handlers': ['websocket_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'leaderboard.views': {
            'handlers': ['performance_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.channels': {
            'handlers': ['websocket_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'gaming_leaderboard.middleware': {
            'handlers': ['performance_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
