from asgitools.routing import (
    AsgiProtocolRouter,
    AsgiProtocol,
    AsgiUrlRouter,
    AsgiUrlRoute
)


with open('index.html', 'rb') as file:
    homepage = file.read()


class WebSocketConsumer:

    def __init__(self, scope):
        self.scope = scope
        self.id = 'ws_consumer:%d' % id(self)

    async def __call__(self, receive, send):
        while True:
            message = await receive()
            if message['type'] == 'websocket.connect':
                await send({'type': 'websocket.accept'})
            elif message['type'] == 'websocket.disconnect':
                return
            elif message['type'] == 'websocket.receive':
                await send({'type': 'websocket.send', 'text': 'Hello world!'})


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


# The protocol router handles parsing the connection scope type in order to
# route the request to an assigned protocol handler. It accepts a list of
# AsgiProtocol definitions.
app = AsgiProtocolRouter([
    # The asgi protocols handle a named scope type (e.g. `http` or `websocket`).
    AsgiProtocol(
        'http',
        # You may include a list of URL routes, but this is not required.
        AsgiUrlRouter([
            # Define a URL route for a consumer class
            AsgiUrlRoute(
                '/', HttpConsumer, methods=['GET']
            ),
        ])
    ),
    AsgiProtocol(
        'websocket',
        WebSocketConsumer
    )
])

# Run with the command `uvicorn app:app`
