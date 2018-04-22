def http_response(scope, body=b'', status=200, headers=[]):
    """Http consumer for simple http responses"""
    async def asgi_instance(receive, send):
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': headers,
        })
        await send({
            'type': 'http.response.body',
            'body': body,
            'more_body': False,
        })
    return asgi_instance
