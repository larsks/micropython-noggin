import json
import socket

# monkeypatch the standard socket module when running
# under cpython.
if not hasattr(socket.socket, 'readline'):
    import noggin.compat.socket
    socket.socket = noggin.compat.socket.mpsocket

try:
    import re
except ImportError:
    import ure as re

try:
    # You can save about 1500 bytes by not including
    # noggin/http.py on your micropython board.
    from noggin.http import HTTP_ERROR_CODES
except ImportError:
    HTTP_ERROR_CODES = {}


def extract_match_groups(match):
    '''Return the available match groups of a ure match object
    as a list'''
    groups = []
    i = 1
    while True:
        try:
            groups.append(match.group(i))
            i += 1
        except IndexError:
            break

    return groups


class HTTPError(Exception):
    '''Request handlers may raise an HTTPError in order to send
    an HTTP error response to the client.

    If status_text is None, it will be filled in with a standard
    description from noggin.http.HTTP_ERROR_CODES.
    '''

    def __init__(self, status_code, status_text=None, content=None):
        self.status_code = status_code

        if status_text is None:
            status_text = HTTP_ERROR_CODES.get(
                status_code, "Unknown status")

        self.status_text = status_text
        self.content = content


class Response():
    '''Request handler functions can return an instance of this class in
    order specify custom headers and response codes.'''

    def __init__(self, status_code=200, status_text=None,
                 content=None, content_type=None, headers=None):

        self.status_code = status_code

        if status_text is None:
            status_text = HTTP_ERROR_CODES.get(
                status_code, "Unknown status")

        self.status_text = status_text
        self.content = content
        self.content_type = content_type
        self.headers = headers


class Request():
    '''Request handlers receive a Request object as their first argument.'''
    bufsize = 256

    def __init__(self, app, method, uri, version, headers, raw):
        self.app = app
        self.method = method.decode('ascii')
        self.uri = uri.decode('ascii')
        self.version = version.decode('ascii')
        self.headers = headers
        self.raw = raw

        self._cached = None
        self._buf = bytearray(self.bufsize)

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

    def _read_n_bytes(self, want):
        have = 0

        if want == 0:
            return

        while True:
            rsize = min(self.bufsize, want - have)
            nb = self.raw.readinto(self._buf, rsize)
            if not nb:
                break
            yield self._buf[:nb]

            have += nb
            if have == want:
                break

    def _read_chunked(self):
        while True:
            length = self.raw.readline().strip()
            length = int(length, 16)

            yield from self._read_n_bytes(length)

            self.raw.readline()
            if length == 0:
                break

    def _read_simple(self):
        length = int(self.headers.get(b'content-length', 0))
        yield from self._read_n_bytes(length)

    def _maybe_send_continue(self):
        if self.headers.get(b'expect') == b'100-continue':
            print('* sending 100 continue response')
            self.send_response(100, 'Continue')

    def iter_content(self):
        self._maybe_send_continue()

        if self.headers.get(b'transfer-encoding') == b'chunked':
            print('* reading chunked content (iter)')
            yield from self._read_chunked()
        else:
            print('* reading simple content (iter)')
            yield from self._read_simple()

    @property
    def content(self):
        if self._cached is None:
            self._cached = bytearray()
            for chunk in self.iter_content():
                self._cached.extend(chunk)

        return bytes(self._cached)

    @property
    def text(self):
        return str(self.content, 'utf-8')


class Noggin():
    '''Noggin (n): 1. A small mug or cup. 2. A simple web application
    framework for MicroPython.'''

    def __init__(self, debug=False):
        self._routes = []
        self._socket = None
        self._debug = debug

    def _create_socket(self, port, backlog):
        self._socket = socket.socket()
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', port))
        self._socket.listen(backlog)

    def _handle_client(self, client, addr):
        print('* handling connection from {}:{}'.format(*addr))

        req = client.readline()
        method, uri, version = (req.split() + [b'HTTP/1.0'])[:3]
        headers = {}

        while True:
            line = client.readline()
            if not line or line == b'\r\n':
                break

            name, value = line.strip().split(b': ')
            headers[name.lower()] = value

        reqobj = Request(self, method, uri, version, headers, client)
        print('* request {}'.format(reqobj))

        try:
            self._handle_request(reqobj)
        except Exception as err:
            print('! Exception: {}'.format(err))
            self.send_response(client, 500, 'Exception',
                               content=str(err))
            raise
        finally:
            reqobj.close()

    def _handle_request(self, req):
        handler, match = self.match(req.uri, req.method)
        if handler:
            groups = extract_match_groups(match)

            try:
                ret = handler(req, *groups)

                if isinstance(ret, (dict, list)):
                    self.send_response(req.raw, 200, 'Okay', json.dumps(ret),
                                       content_type='application/json')
                elif isinstance(ret, Response):
                    self.send_response(req.raw,
                                       ret.status_code,
                                       ret.status_text,
                                       ret.content,
                                       content_type=ret.content_type,
                                       headers=ret.headers)
                else:
                    self.send_response(req.raw, 200, 'Okay', ret)
            except HTTPError as err:
                self.send_response(req.raw, err.status_code, err.status_text,
                                   content=err.content)
        else:
            self.send_response(req.raw, 404, 'Not Found',
                               content='{}: not found'.format(req.uri))

    def send_response(self, sock, status_code, status_text,
                      content=None,
                      content_type=None,
                      headers=None):

        print('* sending reponse {} {}'.format(status_code, status_text))
        lines = []

        lines.append('HTTP/1.1 {} {}\r\n'.format(status_code, status_text))

        if headers:
            for k, v in headers.items():
                lines.append('{}: {}\r\n'.format(k, v))
        if content_type:
            lines.append('Content-type: {}\r\n' .format(content_type))

        if content:
            try:
                clen = len(content)
                lines.append('Content-length: {}\r\n' .format(clen))
            except TypeError:
                pass

        lines.append('\r\n')

        # write out the response header
        for line in lines:
            sock.write(line.encode('ascii'))

        # write out the content
        if content:
            if isinstance(content, str):
                sock.write(content.encode('ascii'))
            elif isinstance(content, (bytes, bytearray)):
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
            self.close()

    def route(self, pattern, methods=['GET']):
        if not pattern.endswith('$'):
            pattern = pattern + '$'

        def _(func):
            self._routes.append((re.compile(pattern), methods, func))
            return func

        return _

    def match(self, uri, method='GET'):
        for route in self._routes:
            match = route[0].match(uri)
            if match:
                if method in route[1]:
                    return route[2], match
        else:
            return None, None

    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None
