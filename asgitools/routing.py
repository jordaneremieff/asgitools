import http

from werkzeug.exceptions import HTTPException
from werkzeug.routing import Rule, Map

from .helpers import http_response


class AsgiProtocol:

    def __init__(self, protocol_type, consumer):
        self.protocol_type = protocol_type
        self.consumer = consumer


class AsgiProtocolRouter:

    def __init__(self, apps):
        self.apps = {app.protocol_type: app for app in apps}

    def __call__(self, scope):
        try:
            protocol = scope['type']
        except KeyError:
            raise Exception('Connection scope missing type')
        try:
            app = self.apps[protocol]
        except KeyError:
            raise Exception('Unhandled protocol type "%s"' % protocol)
        return app.consumer(scope)


class AsgiUrlRoute:

    def __init__(self, path, app, methods=[], name=None):
        if name is None:
            name = 'id<%d>' % id(app)
        self.path, self.app, self.methods, self.name = (path, app, methods, name)


class AsgiUrlRouter:

    def __init__(self, routes):
        self.routes = routes
        mapping = Map([
            Rule(route.path, endpoint=route.name, methods=route.methods)
            for route in routes
        ])
        self.adapter = mapping.bind('')
        self.apps = {route.name: route.app for route in routes}

    def __call__(self, scope):
        path, method = scope['path'], scope.get('method', 'GET')
        if path is None:
            raise Exception('No "path" key in connection scope, routing failed.')
        try:
            endpoint, args = self.adapter.match(path, method)
        except HTTPException as exc:
            status = exc.code
            headers = [[b'content-type', b'text/plain']]
            body = http.HTTPStatus(status).phrase.encode()
            if getattr(exc, 'new_url', ''):
                location = exc.new_url
                if location.startswith('http:///'):
                    location = location[7:]
                headers.append([b'location', location.encode()])
            return http_response(scope, body=body, status=status, headers=headers)
        else:
            scope['args'] = args
            app = self.apps[endpoint]
            return app(scope)
