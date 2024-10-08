import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    raise ImproperlyConfigured('Empty SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split()

if not SECRET_KEY:
    raise ImproperlyConfigured('Empty ALLOWED_HOSTS')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework.authtoken',
    'rest_framework',
    'djoser',
    'core.apps.CoreConfig',
    'api.apps.ApiConfig',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'django'),
        'USER': os.getenv('POSTGRES_USER', 'django'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}

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

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'collected_static'

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {

    'DEFAULT_PAGINATION_CLASS': 'api.paginators.PagePaginationWithLimit',

    'SEARCH_PARAM': 'name',

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],

    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

DJOSER = {
    'LOGIN_FIELD': 'email',
}

DEFAULT_PAGE_SIZE = 6
MAX_USERS_NAMES_LENGTH = 150
MAX_TAGS_NAME = 32
MAX_INGREGIENTS_NAME = 128
MAX_MEASUREMENT_NAME = 64
MAX_EMAIL_LENGTH = 254
MAX_RECIPE_NAME = 256
MIN_COOKING_TIME = 1
MIN_AMOUNT = 1
MSG_SELF_FOLLOW_ERROR = 'CHECK constraint failed: prevent_self_follow'
MSG_ALREADY_SUBSCRIBED_ERROR = (
    'UNIQUE constraint failed: '
    'core_subscription.subscription_id, core_subscription.subscriber_id')
MSG_ALREADY_FAVORE_ERROR = (
    'UNIQUE constraint failed: '
    'core_userrecipefavorite.recipe_id, core_userrecipefavorite.user_id')
MSG_ALREADY_IN_SHOPPING_LIST = (
    'UNIQUE constraint failed: '
    'core_userrecipeshoppinglist.recipe_id, '
    'core_userrecipeshoppinglist.user_id')
ERROR_M2M_CONNECTION_MSGS = {
    MSG_SELF_FOLLOW_ERROR: 'User can\'t subscribe himself',
    MSG_ALREADY_SUBSCRIBED_ERROR: 'You are already subscribed',
    MSG_ALREADY_FAVORE_ERROR: 'You are already favore it',
    MSG_ALREADY_IN_SHOPPING_LIST: 'You are already added it in shoppind list'
}
NOT_CONNECTED_MSG = 'You were not linked that way to it'
