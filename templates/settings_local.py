DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.{{ DB_ENGINE }}',
        'OPTIONS': {
            'db': '{{ DB_NAME }}',
            'user': '{{ DB_NAME }}',
            'passwd': '{{ DB_PASSWORD }}',
            'host': '',
            },
        }
}

STATIC_URL = '/media/static/'
MEDIA_URL = '/media/'

MEDIA_ROOT = '/home/{{ USER }}/webapps/{{ STATIC_APP }}/'
STATIC_ROOT = '/home/{{ USER }}/webapps/{{ STATIC_APP }}/static/'

# Storing caches on filesystem will reduce memory usage
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/home/{{ USER }}/cache',
        }
}
KEY_PREFIX = '{{ APP_NAME }}'
EMAIL_BACKEND = 'webfaction.backends.EmailBackend'

DEBUG = False

from settings import MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES = (
                         'webfaction.middleware.WebFactionFixes',
                         ) + MIDDLEWARE_CLASSES