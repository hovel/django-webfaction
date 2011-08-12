#!/usr/bin/env python
# vim:fileencoding=utf-8

class WebFactionFixes(object):
    """Sets 'REMOTE_ADDR' based on 'HTTP_X_FORWARDED_FOR', if the latter is
    set.
    Based on http://djangosnippets.org/snippets/1706/
    """
    def process_request(self, request):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR'].split(",")[0].strip()
            request.META['REMOTE_ADDR'] = ip
  