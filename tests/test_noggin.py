from unittest import TestCase
from unittest.mock import MagicMock, patch

import noggin


class TestNoggin(TestCase):
    def setUp(self):
        self.app = noggin.Noggin()

    def test_create_app(self):
        assert self.app

    def test_route_simple(self):
        self.app.route('/path1')(MagicMock())
        handler, match = self.app.match('/path1')
        assert handler

    def test_route_params_1(self):
        self.app.route('/path2/([^/]+)')(MagicMock())
        handler, match = self.app.match('/path2/foo')
        assert handler
        assert match.group(1) == 'foo'

    def test_route_params_2(self):
        self.app.route('/path2/([^/]+)')(MagicMock())
        handler, match = self.app.match('/path2/foo/bar')
        assert handler is None

    def test_send_response(self):
        sock = MagicMock()
        self.app.send_response(sock, 200, 'Okay', 'This is a test')
        assert sock.write.called
        assert sock.write.call_args_list[0][0][0] == b'HTTP/1.1 200 Okay\r\n'
        assert sock.write.call_args_list[-1][0][0] == b'This is a test'
