Django-Webfaction
=================

Collection of tools to run django on webfaction more seamless

Installation:
=============

* Install with pip or easy install (pip install django-webfaction)


Usage:
======

Console utility
---------------

Django webfaction contains `webfactionctl` utility that can be used to control your webfaction services from command-line.

1. You get access to basic commands like a list machines/apps/databases/ips/.. and crate apps and databases.
   For example to get list of your current dbs just run::

     webfactionctl list_dbs

2. You can get extended info of your machines with current RAM usage, apps and processes with `state` command::

    $ webfactionctl state
    Query machines list...
    Query apps list...
    Query machine state detail: Web210 Web217 Web223 Web317 Web327
    +-----------+------------------+--------+--------------------+-----------+---------------+-----+
    | ram_usage | operating_system |  name  |      location      | app_count | process_count | id  |
    +===========+==================+========+====================+===========+===============+=====+
    | 209708    | Centos5-32bit    | Web210 | Europe (Amsterdam) | 19        | 20            | 376 |
    +-----------+------------------+--------+--------------------+-----------+---------------+-----+
    | 43112     | Centos5-32bit    | Web217 | Europe (Amsterdam) | 2         | 7             | 386 |
    +-----------+------------------+--------+--------------------+-----------+---------------+-----+
    | 175352    | Centos5-32bit    | Web223 | Europe (Amsterdam) | 12        | 17            | 395 |
    +-----------+------------------+--------+--------------------+-----------+---------------+-----+
    | 8220      | Centos6-64bit    | Web317 | Europe (Amsterdam) | 6         | 7             | 445 |
    +-----------+------------------+--------+--------------------+-----------+---------------+-----+
    | 66092     | Centos6-64bit    | Web327 | Europe (Amsterdam) | 2         | 9             | 462 |
    +-----------+------------------+--------+--------------------+-----------+---------------+-----+

Django deployment wizard
------------------------

With `webfactionctl stup_django_project` you can run django deployment wizard that:

1. Prepare server by installing pip, virtualenv, gunicorn, django-webfaction globally for your account.
2. Create main app for your project
3. Setup virtualenv for your main project
4. Prepare gunicorn contorl script for your project
5. Create static app for your project
6. Prepare settings_local for your project

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

