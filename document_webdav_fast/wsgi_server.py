# -*- coding: utf-8 -*-

import httplib
import logging
import StringIO
import urllib
import openerp

_logger = logging.getLogger(__name__)


def http_to_wsgi(http_dir):
    """
    Turn a BaseHTTPRequestHandler into a WSGI entry point.
    Actually the argument is not a bare BaseHTTPRequestHandler but is wrapped
    (as a class, so it needs to be instanciated) in a HTTPDir.
    This code is adapted from wbsrv_lib.MultiHTTPHandler._handle_one_foreign().
    It is a temporary solution: the HTTP sub-handlers (in particular the
    document_webdav addon) have to be WSGIfied.
    """
    def wsgi_handler(environ, start_response):

        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                key = key[5:].replace('_', '-').title()
                headers[key] = value
            if key == 'CONTENT_LENGTH':
                key = key.replace('_', '-').title()
                headers[key] = value
        if environ.get('Content-Type'):
            headers['Content-Type'] = environ['Content-Type']

        path = urllib.quote(environ.get('PATH_INFO', ''))
        if environ.get('QUERY_STRING'):
            path += '?' + environ['QUERY_STRING']

        request_version = 'HTTP/1.1' # TODO
        request_line = "%s %s %s\n" % (environ['REQUEST_METHOD'], path, request_version)

        class Dummy(object):
            pass

        # Let's pretend we have a server to hand to the handler.
        server = Dummy()
        server.server_name = environ['SERVER_NAME']
        server.server_port = int(environ['SERVER_PORT'])

        # Initialize the underlying handler and associated auth. provider.
        con = openerp.service.websrv_lib.noconnection(environ['wsgi.input'])
        handler = http_dir.instanciate_handler(con, environ['REMOTE_ADDR'], server)

        # Populate the handler as if it is called by a regular HTTP server
        # and the request is already parsed.
        handler.wfile = StringIO.StringIO()
        handler.rfile = environ['wsgi.input']
        handler.headers = headers
        handler.command = environ['REQUEST_METHOD']
        handler.path = path
        handler.request_version = request_version
        handler.close_connection = 1
        handler.raw_requestline = request_line
        handler.requestline = request_line

        # Handle authentication if there is an auth. provider associated to
        # the handler.
        if hasattr(handler, 'auth_provider'):
            try:
                handler.auth_provider.checkRequest(handler, path)
            except openerp.service.websrv_lib.AuthRequiredExc, ae:
                # Darwin 9.x.x webdav clients will report "HTTP/1.0" to us, while they support (and need) the
                # authorisation features of HTTP/1.1 
                if request_version != 'HTTP/1.1' and ('Darwin/9.' not in handler.headers.get('User-Agent', '')):
                    start_response("403 Forbidden", [])
                    return []
                start_response("401 Authorization required", [
                    ('WWW-Authenticate', '%s realm="%s"' % (ae.atype,ae.realm)),
                    # ('Connection', 'keep-alive'),
                    ('Content-Type', 'text/html'),
                    ('Content-Length', 4), # len(self.auth_required_msg)
                    ])
                return ['Blah'] # self.auth_required_msg
            except openerp.service.websrv_lib.AuthRejectedExc,e:
                start_response("403 %s" % (e.args[0],), [])
                return []

        method_name = 'do_' + handler.command

        # Support the OPTIONS method even when not provided directly by the
        # handler. TODO I would prefer to remove it and fix the handler if
        # needed.
        if not hasattr(handler, method_name):
            if handler.command == 'OPTIONS':
                return return_options(environ, start_response)
            start_response("501 Unsupported method (%r)" % handler.command, [])
            return []

        # Finally, call the handler's method.
        try:
            method = getattr(handler, method_name)
            method()
            # The DAV handler buffers its output and provides a _flush()
            # method.
            getattr(handler, '_flush', lambda: None)()
            response = parse_http_response(handler.wfile.getvalue())
            response_headers = response.getheaders()
            body = response.read()
            start_response(str(response.status) + ' ' + response.reason, response_headers)
            return [body]
        except (openerp.service.websrv_lib.AuthRejectedExc, openerp.service.websrv_lib.AuthRequiredExc):
            raise
        except Exception, e:
            print e
            start_response("500 Internal error", [])
            return []

    return wsgi_handler

def parse_http_response(s):
    """ Turn a HTTP response string into a httplib.HTTPResponse object."""
    class DummySocket(StringIO.StringIO):
        """
        This is used to provide a StringIO to httplib.HTTPResponse
        which, instead of taking a file object, expects a socket and
        uses its makefile() method.
        """
        def makefile(self, *args, **kw):
            return self
    response = httplib.HTTPResponse(DummySocket(s))
    response.begin()
    return response

def wsgi_webdav(environ, start_response):
    pi = environ['PATH_INFO']
    if environ['REQUEST_METHOD'] == 'OPTIONS' and pi in ['*','/']:
        return return_options(environ, start_response)
    elif pi.startswith('/webdav'):
        http_dir = openerp.service.websrv_lib.find_http_service(pi)
        if http_dir:
            path = pi[len(http_dir.path):]
            if path.startswith('/'):
                environ['PATH_INFO'] = path
            else:
                environ['PATH_INFO'] = '/' + path
            return http_to_wsgi(http_dir)(environ, start_response)
    return None

openerp.service.wsgi_server.module_handlers.insert(0, wsgi_webdav)
# openerp.service.wsgi_server.register_wsgi_handler(wsgi_webdav)

