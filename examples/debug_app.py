from asgitools.routing import (
    AsgiProtocolRouter,
    AsgiProtocol,
    AsgiUrlRouter,
    AsgiUrlRoute
)

from asgitools.debug import AsgiWsgiDebugMiddleware


class HttpConsumer:

    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        message = await receive()
        if message['type'] == 'http.request':
            raise Exception('Test the debugger!')
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    [b'content-type', b'text/html'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Hello',
                'more_body': False,
            })


app = AsgiProtocolRouter([
    AsgiWsgiDebugMiddleware(
        AsgiProtocol(
            'http',
            AsgiUrlRouter([
                AsgiUrlRoute(
                    '/', HttpConsumer, methods=['GET']
                ),
            ])
        )),
])
