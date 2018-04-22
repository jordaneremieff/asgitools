def message_to_environ(message):
    """
    ASGI message -> WSGI environ
    """
    environ = {
        'REQUEST_METHOD': message['method'],
        'SCRIPT_NAME': message.get('root_path', ''),
        'PATH_INFO': message['path'],
        'QUERY_STRING': message['query_string'].decode('latin-1'),
        'SERVER_PROTOCOL': 'http/%s' % message['http_version'],
        'wsgi.url_scheme': message.get('scheme', 'http'),
    }

    if message.get('client'):
        environ['REMOTE_ADDR'] = message['client'][0]
        environ['REMOTE_PORT'] = str(message['client'][1])
    if message.get('server'):
        environ['SERVER_NAME'] = message['server'][0]
        environ['SERVER_PORT'] = str(message['server'][1])

    headers = dict(message['headers'])
    if b'content-type' in headers:
        environ['CONTENT_TYPE'] = headers.pop(b'content-type')
    if b'content-length' in headers:
        environ['CONTENT_LENGTH'] = headers.pop(b'content-length')
    for key, val in headers.items():
        key_str = 'HTTP_%s' % key.decode('latin-1').replace('-', '_').upper()
        val_str = val.decode('latin-1')
        environ[key_str] = val_str

    return environ


def environ_to_message(environ):
    """
    WSGI environ -> ASGI message
    """
    message = {
        'method': environ['REQUEST_METHOD'].upper(),
        'root_path': environ.get('SCRIPT_NAME', ''),
        'path': environ.get('PATH_INFO', ''),
        'query_string': environ.get('QUERY_STRING', ''),
        'http_version': environ.get('SERVER_PROTOCOL', 'http/1.0').split('/', 1)[-1],
        'scheme': environ.get('wsgi.url_scheme', 'http'),
    }

    if 'REMOTE_ADDR' in environ and 'REMOTE_PORT' in environ:
        message['client'] = [environ['REMOTE_ADDR'], int(environ['REMOTE_PORT'])]
    if 'SERVER_NAME' in environ and 'SERVER_PORT' in environ:
        message['server'] = [environ['SERVER_NAME'], int(environ['SERVER_PORT'])]

    headers = []
    if environ.get('CONTENT_TYPE'):
        headers.append([b'content-type', environ['CONTENT_TYPE'].encode('latin-1')])
    if environ.get('CONTENT_LENGTH'):
        headers.append([b'content-length', environ['CONTENT_LENGTH'].encode('latin-1')])
    for key, val in environ.items():
        if key.startswith('HTTP_'):
            key_bytes = key[5:].replace('_', '-').upper().encode('latin-1')
            val_bytes = val.encode()
            headers.append([key_bytes, val_bytes])

    return message


def status_line_to_status_code(status):
    """
    WSGI status to ASGI status
    """
    return int(status.split()[0])


def status_code_to_status_line(status):
    """
    ASGI status to WSGI status
    """
    try:
        phrase = http.HTTPStatus(status).phrase
    except ValueError:
        phrase = ''
    return '%d %s' % (status, phrase)


def str_headers_to_byte_headers(headers):
    """
    WSGI response_headers to ASGI headers
    """
    return [
        [key.lower().encode('latin-1'), val.encode('latin-1')]
        for key, val in headers
    ]


def byte_headers_to_str_headers(headers):
    """
    ASGI headers to WSGI response_headers
    """
    return [
        (key.decode('latin-1'), val.decode('latin-1'))
        for key, val in headers
    ]
