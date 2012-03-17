__author__ = 'zeus'

import xmlrpclib

class WebfactionAPI(object):
    """
    Simple wrappwer around xmlrpclib for easy iteraction with webfaction services
    """

    def login(self, username, password, machine=None):
        self.server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
        args = [username, password]
        if machine: args.append(machine)
        self.session_id, self.account = self.server.login(*args)

    def __getattr__(self, name):
        return lambda *args: getattr(self.server, name)(self.session_id, *args)