app_name = '{{ APP_NAME }}'
virtualenv_dir_name = '{{ VIRTUALENV_NAME }}'
bind = "0.0.0.0:{{ PORT }}"
logfile = '/home/{{ USER }}/logs/user/{{ APP_NAME }}.log'
loglevel = 'info'
max_requests = 10000
preload_app = True

import os
ROOT = os.path.dirname(os.path.realpath(__file__))
VIRTUAL_ENV = os.path.join(ROOT, virtualenv_dir_name)
django_settings = 'settings'
pythonpath = os.path.join(ROOT, app_name)

# Here we activate virtualenv
# If you have no virtualenv, jsut disable this block or leave virtualenv_dir_name unchanged
if virtualenv_dir_name != '{{ VIRTUALENV_NAME }}':
    activate_this = os.path.join(VIRTUAL_ENV, 'bin/activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))