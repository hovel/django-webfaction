Django-Webfaction
=================

Collection of tools to run django on webfaction more seamless

Installation:
=============

* Install with pip or easy install (pip install django-webfaction)


Usage:
======

Sending mail from local sendmail asynchronous
---------------------------------------------

There is a fail in webfaction deployment, when there is no sendmail server
running on localhost, only smtp server in US. For apps runned in Europe
sending a mail from stmp.webfaction.com or running local sendmail process
takes >1.2 seconds that definately require asynchronous system.

To use asychronous message sending system just add this line to your django settings file::

    EMAIL_BACKEND = 'webfaction.backends.EmailBackend'


Accessing REMOTE_ADDR from django
---------------------------------

When a Django application’s Apache instance proxies requests to Django,
the REMOTE_ADDR header is not set with the clients’s IP address.
Adding this `webfaction.middleware.WebFactionFixes` to your MIDDLEWARE_CLASSES
replace REMOTE_ADDR with correct client's IP.

If you use classic method to modify deployed settings by putting::

    try:
        from settings_local import *
    except ImportError:
        pass

at the end of settings.py file, you can put this code to settings_local::

    MIDDLEWARE_CLASSES = (
       'webfaction.middleware.WebFactionFixes',
    ) + MIDDLEWARE_CLASSES

