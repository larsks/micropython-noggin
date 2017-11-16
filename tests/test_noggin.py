from unittest import TestCase
from unittest.mock import MagicMock, patch

import noggin


def fake_recv_into(self, buf, buflen=0, flags=0):
    c = self.recv(1)
    if c is None:
        return 0

    buf[0] = ord(c)
    return 1


@patch('noggin.compat.socket.mpsocket.recv_into', fake_recv_into)
@patch('noggin.compat.socket.mpsocket.send')
@patch('noggin.compat.socket.mpsocket.recv')
class TestNoggin(TestCase):
    def setUp(self):
        self.app = noggin.Noggin()

    def test_route_simple(self, mock_recv, mock_send):

        '''Does a simple route work as expected?'''

        self.app.route('/path1')(MagicMock())
        handler, match = self.app.match('/path1')
        assert handler

    def test_route_params_1(self, mock_recv, mock_send):

        '''Do routes with match groups work as expected?'''

        self.app.route('/path2/([^/]+)')(MagicMock())
        handler, match = self.app.match('/path2/foo')
        assert handler
        assert match.group(1) == 'foo'

    def test_route_params_2(self, mock_recv, mock_send):

        '''Are routes correctly anchored so that we don't get
        erroneous matches when the initial partial of our request uri
        matches an existing route?'''

        self.app.route('/path2/([^/]+)')(MagicMock())
        handler, match = self.app.match('/path2/foo/bar')
        assert handler is None

    def test_send_response(self, mock_recv, mock_send):

        '''Does calling send_response generate the expected
        content?'''

        sock = MagicMock()
        self.app.send_response(sock, 200, 'Okay', 'This is a test')
        assert sock.write.called
        assert sock.write.call_args_list[0][0][0] == b'HTTP/1.1 200 Okay\r\n'
        assert sock.write.call_args_list[-1][0][0] == b'This is a test'

    def test_request_404(self, mock_recv, mock_send):

        '''If we make a request for a route that doesn't exist, do we
        get a 404 error as expected?'''

        mock_recv.side_effect = (bytes([b]) for b in
                                 b'GET /\r\n\r\n')
        client = noggin.compat.socket.mpsocket()
        self.app._handle_client(client, '1.2.3.4.')

        assert mock_send.called
        assert (mock_send.call_args_list[0][0][0] ==
                b'HTTP/1.1 404 Not Found\r\n')

    def test_request_200(self, mock_recv, mock_send):

        '''Can we successfully handle a request for an existing
        route?'''

        @self.app.route('/')
        def handler(req):
            return 'This is a test'

        mock_recv.side_effect = (bytes([b]) for b in
                                 b'GET /\r\n\r\n')
        client = noggin.compat.socket.mpsocket()
        self.app._handle_client(client, '1.2.3.4.')

        assert mock_send.called
        assert (mock_send.call_args_list[0][0][0] ==
                b'HTTP/1.1 200 Okay\r\n')
        assert (mock_send.call_args_list[-1][0][0] ==
                b'This is a test')

    def test_custom_response(self, mock_recv, mock_send):
        @self.app.route('/')
        def handler(req):
            return noggin.Response(200, 'Custom status',
                                   'This is a test',
                                   content_type='text/html')

        mock_recv.side_effect = (bytes([b]) for b in
                                 b'GET /\r\n\r\n')
        client = noggin.compat.socket.mpsocket()
        self.app._handle_client(client, '1.2.3.4.')

        assert mock_send.called
        assert (mock_send.call_args_list[0][0][0] ==
                b'HTTP/1.1 200 Custom status\r\n')
        assert (mock_send.call_args_list[1][0][0] ==
                b'Content-type: text/html\r\n')

    def test_read_simple(self, mock_recv, mock_send):

        '''Can we correctly read the body of a request?'''

        @self.app.route('/', methods=['PUT'])
        def handler(req):
            return req.content

        mock_recv.side_effect = [
            bytes([b]) for b in
            b'PUT /\r\n'
            b'Content-length: 15\r\n'
            b'\r\n'
            b'This is a test'] + [None]
        client = noggin.compat.socket.mpsocket()
        self.app._handle_client(client, ('1.2.3.4.', 1234))

        assert mock_send.called
        assert (mock_send.call_args_list[0][0][0] ==
                b'HTTP/1.1 200 Okay\r\n')
        assert (mock_send.call_args_list[-1][0][0] ==
                b'This is a test')

    def test_read_chunked(self, mock_recv, mock_send):

        '''Can we correctly read a request using
        Transfer-encoding: chunked?'''

        @self.app.route('/', methods=['PUT'])
        def handler(req):
            return req.content

        mock_recv.side_effect = [
            bytes([b]) for b in
            b'PUT /\r\n'
            b'Transfer-encoding: chunked\r\n'
            b'Content-length: 15\r\n'
            b'\r\n'
            b'E\r\n'
            b'This is a test'
            b'\r\n'
            b'0\r\n'
            b'\r\n'] + [None]
        client = noggin.compat.socket.mpsocket()
        self.app._handle_client(client, ('1.2.3.4.', 1234))

        assert mock_send.called
        assert (mock_send.call_args_list[0][0][0] ==
                b'HTTP/1.1 200 Okay\r\n')
        assert (mock_send.call_args_list[-1][0][0] ==
                b'This is a test')
