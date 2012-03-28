#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import print_function

import argparse
import os.path
from ConfigParser import ConfigParser
import random
import string
import re
from texttable import Texttable
from webfaction.api import WebfactionAPI
import xmlrpclib

__author__ = 'zeus'
__version__ = '0.1'

GUNICORN_CONFIG_TEMPLATE = 'https://raw.github.com/hovel/django-webfaction/master/templates/config.py'
GUNICORN_CONFIG_RUN_SCRIPT = 'https://raw.github.com/hovel/django-webfaction/master/templates/gunicorn.sh'
SETTINGS_LOCAL_TEMPLATE = 'https://raw.github.com/hovel/django-webfaction/master/templates/settings_local.py'


VALID_SYMBOLS = re.compile('^\w+$')

def _gen_password(lfrom=8, lto=10):
    return ''.join((random.choice(string.letters+string.digits) for _ in xrange(random.randint(8,10))))

def _get_config_filename(args):
    if hasattr(args, 'c'):
        return args.c
    return os.path.expanduser('~/.webfactionctl.conf')


def _configure(args):
    config_filename = _get_config_filename(args)
    print('Saving your username and password in %s' % config_filename)
    account = 'user'
    if args.a:
        print('Use account {0}\n \
              To use commands from this account call\n \
              webfactionctl later with -a {0}'.format(args.a))
        account = 'user_{}'.format(args.a)
    if (not args.u) or (not args.p):
        raise ValueError('You should supply username and password (-u, -p options) for using configure')
    config = ConfigParser()
    config.read(config_filename)
    if not config.has_section(account):
        config.add_section(account)
    config.set(account, 'username', args.u)
    config.set(account, 'password', args.p)
    config.write(open(config_filename, 'w'))

def _read_config(args=None):
    config_filename = _get_config_filename(args)
    account = 'user'
    if args.a:
        account = 'user_{}'.format(args.a)
    print('Using account {}'.format(account))
    config = ConfigParser()
    config.read(config_filename)
    username = config.get(account, 'username', None)
    password = config.get(account, 'password', None)
    return username, password

def _login(args=None, machine=None):
    """
    This function can be imported and used in other modules
    therefore it can works without arguments (config usage)
    and have extra machine specification
    """
    if args and args.u and args.p:
        username = args.u
        password = args.p
    else:
        username, password = _read_config(args)
    if (not username) or (not password):
        raise ValueError('Username/password not provided via command line options and not found in config')
    api = WebfactionAPI()
    m = args.m if (args and not machine) else machine
    api.login(username, password, m)
    return api


def _list_query(args):
    what = args.module
    api = _login(args)
    rows = getattr(api, 'list_%s' % what)()
    if not rows:
        print('No %s found' % what)
        return
    table = Texttable(max_width=140)
    table.add_rows([rows[0].keys()] + [row.values() for row in rows])
    print(table.draw())

def _create_app(args):
    api = _login(args)
    response = api.create_app(args.name, args.type, args.autostart, args.extra_info)
    print('App has been created:')
    table = Texttable(max_width=140)
    table.add_rows([['Param', 'Value']] + [[key, value] for key, value in response.items()])
    print(table.draw())

def _delete_app(args):
    api = _login(args)
    api.delete_app(args.name)

def _create_db(args):
    if (len(args.name) > 16) and (args.db_type == 'mysql'):
        print('Error: MySQL database names may not exceed 16 characters, including the username prefix')
        return
    ags = [args.name, args.db_type]
    if args.password:
        ags.append(args.password)
    else:
        password = _gen_password()
        print('Password not provided, so I generate a password for you:\n%s' % password)
        ags.append(password)
    api = _login(args)
    response = api.create_db(*ags)
    print('Database %s has been created' % args.name)
    table = Texttable(max_width=140)
    table.add_rows([['Param', 'Value']] + [[key, value] for key, value in response.items()])
    print(table.draw())

def _delete_db(args):
    api = _login(args)
    api.delete_db(args.name, args.db_type)

def _state(args):
    """
    Verbose, since some operations a very slow
    """
    api = _login(args)
    username, password = _read_config(args)
    print('Query machines list...')
    machines = api.list_machines()
    print('Query apps list...')
    apps = api.list_apps()
    print('Query machine state detail: ', end='')
    for m in machines:
        print('%s ' % m['name'], end='')
        api = _login(args, m['name'])
        m['ram_usage'] = api.system("ps -u %s -o rss,command | awk 'FNR>-1 { sum+=$1 } END {print sum}'" % username)
        m['process_count'] = api.system("ps -u %s | wc -l" % username)
        m_apps = [app for app in apps if app['machine']==m['name']]
        m['app_count'] = len(m_apps)
    print('')
    table = Texttable(max_width=140)
    table.add_rows([machines[0].keys()] + [row.values() for row in machines])
    print(table.draw())

def _setup_django_project(args):
    print('\nLet\'s prepare your app and webfaction for launch!\n')
    username, password = _read_config(args)
    api = _login(args)
    ms = api.list_machines()
    m_names = [m['name'] for m in ms]
    print('On which machine you want to place your app?')
    print('You have this machines on your account: %s' % (' '.join(m_names)))
    target_machine = None
    while not target_machine:
        target_machine = raw_input('Enter machine name or press enter to list detail machines state: ')
        if target_machine == '':
            _state(args)
            target_machine = None
            continue
        if target_machine not in m_names:
            print('\nYou have no account on machine with this name!\n')
            print('You have this machines on your account: %s' % (' '.join(m_names)))
            target_machine = None
    print('\nNew app will be placed on %s\n' % target_machine)

    try:
        pip = api.system('ls -l ~/bin/pip-2.7')
    except xmlrpclib.Fault:
        pip = None
    prepare_machine = False
    recommend_prepare = 'N'
    if not pip:
        print('Looks like this server doesn\'t prepared for django project')
        recommend_prepare = 'Y'
    print('It\'s recommend to have pip, virtualenv, djagno-webfaction and mercurial')
    print('for python 2.7 to be installed')
    print('I can install this tools for you, if you want')
    prepare_machine = raw_input('Should i do it? Y/N [%s]: ' % recommend_prepare)
    prepare_machine = (recommend_prepare=='Y') if not prepare_machine else (prepare_machine=='Y')

    app_name = None
    api = _login(args, machine=target_machine)
    apps = api.list_apps()
    a_names = [a['name'] for a in apps]
    while not app_name:
        app_name = raw_input('Please enter new name for your application: ')
        if app_name in a_names:
            print('You already have app with same name, choose another one')
            app_name = None
            continue
        if not VALID_SYMBOLS.match(app_name):
            print('App name that you enter is not valid (use A-Z a-z 0-9 or uderscore symbols only)')
            app_name = None
    print('\nNew app will named as %s' % app_name)
    print('This app will live in /home/%s/webapps/%s/\n' % (username, app_name))
    print('This directory will contain a gunicorn run script,')
    print('a gunicorn config and your directory with your project')

    project_name = raw_input('Please, tell me how you call your project [%s]: ' % app_name)

    print('\nIf your django app contains static files (typical) they should be serverd')
    print('by front-end server (nginx) directy, in webfaction this means to create')
    print('a special \'static\' application that will contain static files')
    print('I will help you to configure your app to use this app at the end of')
    print('installation process.')
    create_static = static_app_name = None
    while not (create_static=='Y' or create_static=='N'):
        create_static = raw_input('Should i create static app for you? Y/N [Y]: ')
        if not create_static:
            create_static = 'Y'
    create_static = True if create_static=='Y' else False
    if create_static:
        static_app_name = None
        default_static_app_name = '%s_static' % app_name
        while not static_app_name:
            static_app_name = raw_input('How should i call static app? [%s]' % default_static_app_name)
            if not static_app_name:
                static_app_name = default_static_app_name
                break
            if static_app_name in a_names:
                print('You already have app with same name, choose another one')
                static_app_name = None
                continue
            if not VALID_SYMBOLS.match(app_name):
                print('App name that you enter is not valid (use A-Z a-z 0-9 or uderscore symbols only)')
                static_app_name = None

    create_env = None
    while not(create_env=='Y' or create_env=='N'):
        create_env = raw_input('Should i create a virtualenv for your project (recommended)? Y/N [Y]: ')
        if not create_env:
            create_env = 'Y'
    create_env = True if create_env=='Y' else False

    create_db = db_type = db_name = db_password = None
    while not(create_db=='Y' or create_db=='N'):
        create_db = raw_input('Should i create a db for your project (recommended)? Y/N [Y]: ')
        if not create_db:
            create_db = 'Y'
    create_db = True if create_db=='Y' else False
    if create_db:
        #TODO validate db_name and type
        print('Note: all database names for your account should be prefixed with your username')
        db_name = '%s_%s' % (username, raw_input('Please enter a name for new database: %s_' % username))
        db_type = raw_input('Please specify database type (mysql/posgress) [mysql]: ')
        if not db_type:
            db_type = 'mysql'
        random_passwd = _gen_password()
        db_password = raw_input('Please choose a password for your database [%s]: ' % random_passwd)
        if not db_password:
            db_password = random_passwd

    print('\n\nSo, i will do this tasks for you:')
    print('-------------------------------')
    if prepare_machine:
        print('I will install pip, virtualenv, django-webfaction and' \
              ' mercurial for python 2.7 on %s' % target_machine)
    print('Install gunicorn globally for python 2.7')
    print('Create new app %s on %s for django' % (app_name, target_machine))
    if create_static:
        print('Create new app %s on %s for serving static files' % (static_app_name, target_machine))
    if create_db:
        print('Create %s database %s on %s' % (db_type, db_name, target_machine))
    if create_env:
        print('I will create virtualenv in ~/webapps/%s/env' % app_name)
    print('--------------------------------')
    print('I will also place next files in ~/webapps/%s' % app_name)
    print('gunicorn.sh - script that can be used to start/stop/restart app')
    print('config.py - config for gunicorn and configure it for your new app')
    print('settigs_local.py - a settings file for your new app')

    ctn = raw_input('Should i continue? Y/N [Y]: ')
    if ctn not in ['', 'Y']:
        print('Ok, buy!')
        return

    if prepare_machine:
        print('Prepearing your system...')
        api.system('mkdir ~/lib/python2.7')
        api.system('easy_install-2.7 pip')
        api.system('~/bin/pip-2.7 install virtualenv mercurial django-webfaction')
    print('Installing gunicorn...')
    api.system('~/bin/pip-2.7 install gunicorn')
    print('Creating custom app with port %s..' % app_name)
    app_info = api.create_app(app_name, 'custom_app_with_port', False, '')
    print(app_info)
    if create_env:
        venv_path = '~/webapps/%s/env' % app_name
        print('Creating virtualenv at %s...' % venv_path)
        api.system('~/bin/virtualenv --system-site-packages %s' % venv_path)
    if create_static:
        print('Creating static app...')
        api.create_app(static_app_name, 'static_only', False, '')

    if create_db:
        print('Creating database')
        api.create_db(db_name, db_type, db_password)
    print('Loading gunicorn control scrpit, config and settings_local templates')
    api.system('wget %s -q -O ~/webapps/%s/config.py' % (GUNICORN_CONFIG_TEMPLATE, app_name))
    api.system('wget %s -q -O ~/webapps/%s/gunicorn.sh' % (GUNICORN_CONFIG_RUN_SCRIPT, app_name))
    api.system('wget %s -q -O ~/webapps/%s/settings_local.py' % (SETTINGS_LOCAL_TEMPLATE, app_name))
    for rep in [
        ('{{ USER }}', username),
        ('{{ APP_NAME }}', app_name),
        ('{{ PORT }}', app_info['port'])
    ]:
        api.replace_in_file('/home/%s/webapps/%s/config.py' % (username, app_name), rep)
    if create_env:
        api.replace_in_file('/home/%s/webapps/%s/config.py' % (username, app_name), ('{{ VIRTUALENV_NAME }}', venv_path))


    for rep in [
        ('{{ USER }}', username),
        ('{{ APP_NAME }}', app_name),
        ('{{ DB_NAME }}', db_name),
        ('{{ DB_ENGINE }}', db_type),
        ('{{ DB_PASSWORD }}', db_password),
        ('{{ STATIC_APP }}', static_app_name),
    ]:
        if rep:
            api.replace_in_file('/home/%s/webapps/%s/settings_local.py' % (username, app_name), rep)

    print('\nOk, now you are just a two step away from deploy your project on webfaction server')
    print('1. Copy/clone your project to ~/webapps/%s/' % app_name)
    print('2. Copy ~/webapps/%s/settings.py to your project directory and ensure that your settings.py import * from settings_local.py at the end')
    print('3. You\'re done! You can do syncdb/migrate/collectstatic...')
    # TODO: Download fabfile template

def main():
    parser = argparse.ArgumentParser(description="Control webfaction servers via API")
    subparsers = parser.add_subparsers()
    parser.add_argument('-u', help='username for connection (required if not stored in config)')
    parser.add_argument('-p', help='password for connection (required if not stored in config)')
    parser.add_argument('-m', help='machine to access (can be omitted to work with default machine)')
    parser.add_argument('-a', help='account (if multiple accounts (username/passwords paris) is used,\n' \
                                   ' specify during `configure` to save username and password pair as\n' \
                                   ' a other than default account and use later to work with this account)')

    cmd = subparsers.add_parser('configure', help='Store security credentials in local config')
    cmd.set_defaults(func=_configure)
    for module in ['apps', 'domains', 'websites', 'dbs', 'machines', 'ips', 'users', 'emails', 'mailboxes', 'list_dns_overrides']:
        cmd = subparsers.add_parser('list_%s' % module, help='List your %s on webfaction' % module)
        cmd.set_defaults(func=_list_query)
        cmd.set_defaults(module=module)

    cmd = subparsers.add_parser('create_app', help='Create a new application')
    cmd.set_defaults(func=_create_app)
    cmd.add_argument('name', help="Unique name for new app")
    cmd.add_argument('type',
        help="Application type (typical 'custom_app_with_port' or 'static_only')")
    cmd.add_argument('--autostart', default=False,
        help = "Whether the app should restart with an autostart.cgi script")
    cmd.add_argument('--extra_info', default='',
        help="Additional information required by the application")

    cmd = subparsers.add_parser('delete_app', help='Delete an application')
    cmd.set_defaults(func=_delete_app)
    cmd.add_argument('name', help='name of the application')

    cmd = subparsers.add_parser('create_db', help='Create a database')
    cmd.set_defaults(func=_create_db)
    cmd.add_argument('name', help='database name')
    cmd.add_argument('db_type', help="database type ('mysql' or 'postgresql')")
    cmd.add_argument('--password', help='password for database (if omitted, will be generated)')

    cmd = subparsers.add_parser('delete_db', help='Delete a database')
    cmd.set_defaults(func=_delete_db)
    cmd.add_argument('name', help='database name')
    cmd.add_argument('db_type', help="database type ('mysql' or 'postgresql')")

    cmd = subparsers.add_parser('state', help='Short state of your machines (apps count, current ram usage)')
    cmd.set_defaults(func=_state)

    cmd = subparsers.add_parser('setup_django_project', help='prepare server, create virtualenv, create apps (django itself, static), create db on server, create settings_local for server, setup and prepare gunicorn, setup cronjob')
    cmd.set_defaults(func=_setup_django_project)


    # Call selected function
    args = parser.parse_args()
    args.func(args)

