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

__author__ = 'zeus'
__version__ = '0.1'

VALID_SYMBOLS = re.compile('^\w+$')

def _get_config_filename(args):
    if hasattr(args, 'c'):
        return args.c
    return os.path.expanduser('~/.webfactionctl.conf')


def _configure(args):
    config_filename = _get_config_filename(args)
    print('Saving your username and password in %s' % config_filename)
    if (not args.u) or (not args.p):
        raise ValueError('You should supply username and password (-u, -p options) for using configure')
    config = ConfigParser()
    config.read(config_filename)
    if not config.has_section('user'):
        config.add_section('user')
    config.set('user', 'username', args.u)
    config.set('user', 'password', args.p)
    config.write(open(config_filename, 'w'))

def _read_config(args=None):
    config_filename = _get_config_filename(args)
    config = ConfigParser()
    config.read(config_filename)
    username = config.get('user', 'username', None)
    password = config.get('user', 'password', None)
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
        username, password = _read_config()
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
        password = ''.join((random.choice(string.letters+string.digits) for _ in xrange(random.randint(8,10))))
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

    app_name = None
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
    print('\nNew app will named as %s\n' % app_name)

    print('If your django app contains static files (typical) they should be serverd')
    print('by front-end server (nginx) directy, in webfaction this means to create')
    print('a special \'static\' application that will contain static files')
    print('I will help you to configure your app to use this app at the end of')
    print('installation process.')
    create_static = None
    while create_static=='Y' or create_static=='N':
        create_static = raw_input('Should i create static app for you? [Y]')
        if not create_static:
            create_static = 'Y'
    create_static = True if create_static=='Y' else False
    if create_static:
        static_app_name = None
        while not static_app_name:
            static_app_name = raw_input('How should i call static app? [%s_staic]' % app_name)
            if static_app_name in a_names:
                print('You already have app with same name, choose another one')
                static_app_name = None
                continue
            if not VALID_SYMBOLS.match(app_name):
                print('App name that you enter is not valid (use A-Z a-z 0-9 or uderscore symbols only)')
                static_app_name = None

    create_env = None
    while create_env=='Y' or create_env=='N':
        create_env = raw_input('Should i create a virtualenv for your project (recommended)?[Y]')
        if not create_env:
            create_env = 'Y'
    create_env = True if create_env=='Y' else False




def main():
    parser = argparse.ArgumentParser(description="Control webfaction servers via API")
    subparsers = parser.add_subparsers()
    parser.add_argument('-u', help='username for connection (required if not stored in config)')
    parser.add_argument('-p', help='password for connection (required if not stored in config)')
    parser.add_argument('-m', help='machine to access (can be omitted to work with default machine)')
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

#    cmd = subparsers.add_parser('setup_django_project', help='prepare server, create virtualenv, create apps (django itself, static), create db on server, create settings_local for server, setup and prepare gunicorn, setup cronjob')
#    cmd.set_defaults(func=_setup_django_project)


    # Call selected function
    args = parser.parse_args()
    args.func(args)

