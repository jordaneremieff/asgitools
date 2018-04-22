from werkzeug.debug import DebuggedApplication
from werkzeug.debug.tbtools import get_current_traceback

from asgiref.sync import sync_to_async

from . import utils
from .helpers import http_response


class AsgiWsgiDebugMiddleware(DebuggedApplication):

    def __init__(self, *args, **kwargs):
        self.protocol_type = 'http'
        # os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        super().__init__(*args, **kwargs)
        self.scope = None

    def consumer(self, scope):
        environ = utils.message_to_environ(scope)
        wsgi_status = None
        wsgi_headers = None

        def start_response(status, headers, exc_info=None):
            nonlocal wsgi_status, wsgi_headers
            wsgi_status = status
            wsgi_headers = headers

        response = super().__call__(environ, start_response)
        if response is None:
            return self._debug_application(scope)
        else:
            # Requests to the debugger.
            # Eg. load resource, pin auth, issue command.
            status = utils.status_line_to_status_code(wsgi_status)
            headers = utils.str_headers_to_byte_headers(wsgi_headers)
            body = b''.join(response)
            return http_response(scope, body=body, status=status, headers=headers)

    def debug_application(self, environ, start_response):
        return None

    def _debug_application(self, scope):
        self.scope = scope
        app = self.app.consumer(scope)

        async def asgi_wrapper(receive, send):
            try:
                return await app(receive, send)
            except Exception:
                traceback = get_current_traceback(
                    skip=1, show_hidden_frames=self.show_hidden_frames,
                    ignore_system_exceptions=True
                )
                for frame in traceback.frames:
                    self.frames[frame.id] = frame
                self.tracebacks[traceback.id] = traceback
                environ = utils.message_to_environ(self.scope)
                is_trusted = sync_to_async(self.check_pin_trust)(environ)
                _traceback = traceback.render_full(
                    evalex=self.evalex,
                    evalex_trusted=is_trusted,
                    secret=self.secret
                ).encode('utf-8', 'replace')
                headers = [
                    (b'Content-Type', b'text/html; charset=utf-8'),
                    # Disable Chrome's XSS protection, the debug
                    # output can cause false-positives.
                    (b'X-XSS-Protection', b'0'),
                ]
                response = http_response(self.scope, body=_traceback, status=500, headers=headers)
                return await response(receive, send)
        return asgi_wrapper
