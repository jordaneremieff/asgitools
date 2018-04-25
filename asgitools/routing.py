import http

from werkzeug.exceptions import HTTPException
from werkzeug.routing import Rule, Map

from .helpers import http_response


class AsgiProtocol:

    def __init__(self, protocol_type, protocol_handler):
        self.protocol_type = protocol_type
        self.protocol_handler = protocol_handler

    def __call__(self, scope):
        return self.protocol_handler(scope)
        

class AsgiProtocolRouter:

    def __init__(self, protocols):
        self.protocols = {protocol.protocol_type: protocol for protocol in protocols}

    def __call__(self, scope):
        try:
            protocol_type = scope['type']
        except KeyError:
            raise Exception('Connection scope missing type')
        try:
            protocol = self.protocols[protocol_type]
        except KeyError:
            raise Exception('Unhandled protocol type "%s"' % protocol_type)
        return protocol(scope)


class AsgiUrlRoute:

    def __init__(self, path, consumer, methods=['GET'], name=None):
        if name is None:
            name = 'id<%d>' % id(consumer)
        self.path, self.consumer, self.methods, self.name = (path, consumer, methods, name)


class AsgiUrlRouter:

    def __init__(self, routes):
        self.routes = routes
        mapping = Map([
            Rule(route.path, endpoint=route.name, methods=route.methods)
            for route in routes
        ])
        self.adapter = mapping.bind('')
        self.routes = {route.name: route.consumer for route in routes}

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
            consumer = self.routes[endpoint]
            try:
                consumer.middlewares
            except AttributeError:
                print("OK")
                return consumer(scope)
            middleware_router = AsgiMiddlewareRouter(consumer, scope)
            return middleware_router(scope)


class AsgiMiddlewareRouter:

    def __init__(self, consumer, scope):
        self.consumer = consumer
        self.scope = scope
        self.middleware_instances = []
        self.asgi_instance = None
        self.send = None

    def __call__(self, scope):
        """Create middleware instances for the scope"""
        self.scope = scope
        asgi_instance = self.consumer(self.scope)
        for middleware in self.consumer.middlewares:
            self.middleware_instances.append(middleware(asgi_instance, self.scope))

        async def asgi_wrapper(receive, send):
            self.send = send
            return await asgi_instance(receive, self.middleware_send)
        return asgi_wrapper

    async def middleware_send(self, message):
        """
        Override the send to allow the middlewares to handle messages.
        """
        for middleware in self.middleware_instances:
            # If the middleware alters the message, return the modified version
            _message = await middleware(message)
            if _message:
                message = _message
        return await self.send(message)
