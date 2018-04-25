from asgitools.routing import (
    AsgiProtocolRouter,
    AsgiProtocol,
    AsgiUrlRouter,
    AsgiUrlRoute,
    AsgiMiddlewareRouter
)
from asgitools.debug import AsgiWsgiDebuggedApplication
from asgitools.middlewares.broadcast import BroadcastMiddleware


with open('index.html', 'rb') as file:
    homepage = file.read()


class WebSocketConsumer:

    middlewares = [BroadcastMiddleware]

    def __init__(self, scope):
        self.scope = scope
        self.groups = None

    async def __call__(self, receive, send):
        self.send = send
        while True:
            message = await receive()

            if message['type'] == 'websocket.connect':
                await send({'type': 'websocket.accept'})
                await self.groups.send({
                    'group': 'chat',
                    'add': self.id
                })

            elif message['type'] == 'websocket.receive':
                text = '<%s> %s' % (self.id, message['text'])
                await self.groups.send({
                    'group': 'chat',
                    'send': {'type': 'websocket.send', 'text': text}
                })

            elif message['type'] == 'websocket.disconnect':
                await self.groups.send({
                    'group': 'chat',
                    'discard': self.id
                })


class HttpConsumer:

    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        message = await receive()
        if message['type'] == 'http.request':
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    [b'content-type', b'text/html'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': homepage,
                'more_body': False,
            })


app = AsgiProtocolRouter([
    AsgiProtocol(
        'http',
        AsgiUrlRouter([
            AsgiUrlRoute(
                '/', HttpConsumer, methods=['GET']
            ),
        ]),
    ),
    AsgiProtocol(
        'websocket',
        AsgiUrlRouter([
            AsgiUrlRoute(
                '/ws/', WebSocketConsumer
            ),
        ]),
    ),
])

app = AsgiWsgiDebuggedApplication(app)


# Run with the command `uvicorn app:app` or `daphne app:app`
