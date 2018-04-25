# asgitools

A collection of tools for developing [ASGI] applications. Supports both ASGI servers, [uvicorn] and [daphne].

**Requirements**: Python 3.5.3+ and an ASGI server

Currently includes:

- Protocol and URL routing
- WSGI debug middleware
- Redis broadcast middleware

## Quickstart

You can find an example app in `examples/` that demonstrates protocol, url routing, middleware usage, and wsgi debugger.

Otherwise you can try the example below to run a simple HTTP app:

Install using `pip`:

- TODO

Create an application, in `app.py`:

```python
from asgitools.routing import (
    AsgiProtocolRouter,
    AsgiProtocol,
    AsgiUrlRouter,
    AsgiUrlRoute
)


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
                'body': b'Hello world!',
                'more_body': False,
            })


app = AsgiProtocolRouter([
    AsgiProtocol(
        'http',
        AsgiUrlRouter([
            AsgiUrlRoute(
                '/', HttpConsumer, methods=['GET']
            ),
        ])
    ),
])

```

Run the server:

```shell
$ uvicorn app:app
```

OR

```shell
$ daphne app:app
```
---

# Todo

- Tests
- Middleware
- Better examples

[ASGI]: https://github.com/django/asgiref/blob/master/specs/asgi.rst
[uvicorn]: https://github.com/encode/uvicorn
[daphne]: https://github.com/django/daphne
