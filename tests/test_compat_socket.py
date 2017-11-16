from unittest import TestCase
from unittest.mock import MagicMock, patch

import noggin.compat.socket


class fakesocket():
    def __init__(self, *args, **kwargs):
        self.recv = MagicMock()
        self.recv.side_effect = (bytes([b]) for b in b'hello\nworld\n')

        self.send = MagicMock()


class TestCompatSocket(TestCase):
    def test_readline(self):
        with patch('noggin.compat.socket.mpsocket.recv') as recv:
            recv.side_effect = (bytes([b]) for b in b'hello\nworld\n')
            s = noggin.compat.socket.mpsocket()
            line = s.readline()
            assert recv.call_count == len(b'hello\n')
            assert line == b'hello\n'

    def test_write(self):
        with patch('noggin.compat.socket.mpsocket.send') as send:
            s = noggin.compat.socket.mpsocket()
            s.write('hello world')
            assert send.called
            assert send.call_args[0][0] == 'hello world'

    def test_read(self):
        with patch('noggin.compat.socket.mpsocket.recv') as recv:
            s = noggin.compat.socket.mpsocket()
            s.read(1024)
            assert recv.called
            assert recv.call_args[0][0] == 1024
