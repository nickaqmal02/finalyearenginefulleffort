import os
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o%*b0^*_*#k&a@*up)d*l%!sxn^hms8y_&i$+zl46r_&p3mzp%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DEBUG_TOOLBAR_PANELS = []

INTERNAL_IPS = [
    "127.0.0.1",
]

ALLOWED_HOSTS = ['*']

CSRF_COOKIE_SECURE = False 
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = []

# Application definition

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'heroicons',
    'debug_toolbar',
    'django_extensions',
    'crispy_forms',
    #'crispy_tailwind',
    'django_tailwind_cli',
    'chat_analyzer'
]

#crispy forms configuration TAILWIND
CRISPY_ALLOWED_TEMPLATE_PACKS = "unfold_crispy"
CRISPY_TEMPLATE_PACK = ["unfold_crispy"]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'finalyearengineredo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'finalyearengineredo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "assets",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Enable DaisyUI (optional but you wanted it)
TAILWIND_CLI_USE_DAISY_UI = True

# admin registeration invite code (change this to something more secure )
ADMIN_INVITE_CODE = 'AutismCenter2024!Secure123'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'chat_analyzer.User'


# ====================================
# UNFOLD ADMIN THEME CONFIGURATION
# ====================================
UNFOLD = {
    "SITE_TITLE": "Sentiri Admin",
    "SITE_HEADER": "Sentiri Admin",
    "SITE_ICON": "https://avatars.githubusercontent.com/u/134147465?s=200&v=4",
    "COLORS": {
        "primary": {
            50: "#ecfdf5", 100: "#d1fae5", 200: "#a7f3d0", 300: "#6ee7b7",
            400: "#34d399", 500: "#10b981", 600: "#059669", 700: "#047857",
            800: "#065f46", 900: "#064e3b", 950: "#022c22",
        },
        "base": {
            50: "#f8fafc", 100: "#f1f5f9", 200: "#e2e8f0", 300: "#cbd5e1",
            400: "#94a3b8", 500: "#64748b", 600: "#475569", 700: "#334155",
            800: "#1e293b", 900: "#0f172a", 950: "#020617",
        },
        "font": {
            "subtle-light": "#94a3b8",
            "subtle-dark": "#64748b",
            "default-light": "#475569",
            "default-dark": "#cbd5e1",
            "important-light": "#0f172a",
            "important-dark": "#f1f5f9",
        },
    },
    "BORDER_RADIUS": {
        "xs": "0.125rem",
        "sm": "0.25rem",
        "default": "0.375rem",
        "md": "0.375rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Dashboard"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Analytics Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ]
            },
            {
                "title": _("Clients"),
                "separator": False,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Client Cards"),
                        "icon": "group",
                        "link": reverse_lazy("admin:chat_analyzer_client_cards"),
                    },
                ]
            }
        ]
    },
    "DASHBOARD_CALLBACK": "chat_analyzer.dashboard.dashboard_callback",
}


