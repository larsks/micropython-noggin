import json
import socket

try:
    import re
except ImportError:
    import ure as re

import noggin.http


class HTTPError(Exception):

    def __init__(self, status_code, status_text=None, content=None):
        self.status_code = status_code

        if status_text is None:
            status_text = noggin.http.HTTP_ERROR_CODES.get(
                status_code, "Unknown error")

        self.status_text = status_text
        self.content = content


class Response():
    def __init__(self, status_code=200, status_text=None,
                 content=None, mimetype=None, headers=None):

        self.status_code = status_code

        if status_text is None:
            status_text = noggin.http.HTTP_ERROR_CODES.get(
                status_code, "Unknown error")

        self.status_text = status_text
        self.content = content
        self.mimetype = mimetype
        self.headers = headers


class Request():
    def __init__(self, app, method, uri, version, headers, raw):
        self.app = app
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers
        self.raw = raw

        self._after = []
        self._cached = None

    def __str__(self):
        return '<{} {}>'.format(self.method, self.uri)

    def send_response(self, *args, **kwargs):
        self.app.send_response(self.raw, *args, **kwargs)

    def close(self):
        print('* closing request')
        if self.raw:
            self.raw.close()
            self.raw = None

        self._cached = None

    def _read_chunked(self):
        _content = bytearray()
        while True:
            length = self.raw.readline().strip()
            print('* reading chunk length = {}'.format(length))
            length = int(length, 16)
            data = self.raw.read(length)
            self.raw.readline()
            if length == 0:
                break
            print('* read data: {}'.format(repr(data)))
            _content.extend(data)

        return bytes(_content)

    def _read_simple(self):
        length = int(self.headers.get(b'content-length', 0))
        if length == 0:
            return ''

        return self.raw.read(length)

    @property
    def content(self):
        if self._cached is None:
            if self.headers.get(b'expect') == b'100-continue':
                print('* sending 100 continue response')
                self.send_response(100, 'Continue')

            if self.headers.get(b'transfer-encoding') == b'chunked':
                print('* reading chunked content')
                self._cached = self._read_chunked()
            else:
                print('* reading simple content')
                self._cached = self._read_simple()
        return self._cached

    @property
    def text(self):
        return str(self.content, 'utf-8')


class App():

    def __init__(self):
        self._routes = []

    def _create_socket(self, port, backlog):
        self._socket = socket.socket()
        self._socket.bind(('', port))
        self._socket.listen(backlog)

    def _handle_client(self, client, addr):
        print('* handling connection from {}:{}'.format(*addr))
        req = client.readline()
        method, uri, version = (req.split() + ['HTTP/1.0'])[:3]
        headers = {}

        while True:
            l = client.readline()
            if not l or l == b'\r\n':
                break

            name, value = l.strip().split(b': ')
            print('* setting header {} = {}'.format(name.lower(), value))
            headers[name.lower()] = value

        reqobj = Request(self, method, uri, version, headers, client)
        print('* got request object {}'.format(reqobj))

        try:
            self._handle_request(reqobj)
        except Exception as err:
            self.send_response(client, 500, 'Exception',
                               content=str(err))
        finally:
            reqobj.close()

    def _handle_request(self, req):
        handler, match = self.match(req.uri, req.method)
        if handler:
            try:
                ret = handler(req, match)
            except HTTPError as err:
                self.send_response(req.raw, err.status_code, err.status_text,
                                   content=err.content)
            else:
                if isinstance(ret, dict):
                    self.send_response(req.raw, 200, 'Okay', json.dumps(ret),
                                       mimetype='application/json')
                elif isinstance(ret, Response):
                    self.send_response(req.raw,
                                       ret.status_code,
                                       ret.status_text,
                                       ret.content,
                                       mimetype=ret.mimetype,
                                       headers=ret.headers)
                else:
                    self.send_response(req.raw, 200, 'Okay', ret)
        else:
            self.send_response(req.raw, 404, 'Not Found',
                               content='{}: not found'.format(req.uri))

    def send_response(self, sock, status_code, status_text,
                      content=None,
                      mimetype=None,
                      headers=None):

        print('* sending reponse {} {}'.format(status_code, status_text))

        sock.write('HTTP/1.1 {} {}\r\n'.format(
            status_code, status_text))

        if headers:
            for k, v in headers.items():
                sock.write('{}: {}\r\n'.format(k, v))
        if mimetype:
            sock.write('Content-type: {}\r\n'.format(mimetype))
        if content:
            try:
                clen = len(content)
                sock.write('Content-length: {}\r\n'.format(clen))
            except TypeError:
                pass

        sock.write('\r\n')

        if content:
            if isinstance(content, (str, bytes)):
                sock.write(content)
            else:
                for chunk in content:
                    sock.write(chunk)

    def serve(self, port=80, backlog=1):
        try:
            self._create_socket(port, backlog)

            while True:
                client, addr = self._socket.accept()
                try:
                    self._handle_client(client, addr)
                except OSError as err:
                    print('! error handling client {}:{}: {}'.format(
                        addr[0], addr[1], err))
        finally:
            if self._socket is not None:
                self._socket.close()

    def route(self, pattern, method='GET'):
        if not pattern.endswith('$'):
            pattern = pattern + '$'

        def _(func):
            self._routes.append((re.compile(pattern),
                                 bytes(method, 'ascii'), func))
            return func

        return _

    def match(self, uri, method='GET'):
        for route in self._routes:
            match = route[0].match(uri)
            if match:
                if route[1].lower() == method.lower():
                    return route[2], match
        else:
            return False, None
