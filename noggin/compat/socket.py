'''This module is used to monkeypatch the standard CPython "socket" module
in order to provide compatability with the micropython API.'''

import socket


class mpsocket(socket.socket):
    '''Additional methods found on the MicroPython usocket.socket
    class.'''

    def readline(self):
        '''Read a line, ending in a newline character.'''

        line = bytearray()
        while True:
            c = self.recv(1)

            if c is None:
                break

            line.extend(c)
            if line.endswith(b'\n'):
                break

        return bytes(line)

    def write(self, buf):
        '''Write the buffer of bytes to the socket.

        This is just a wrapper around self.send(buf).
        '''
        return self.send(buf)

    def read(self, size):
        '''Read up to size bytes from the socket.

        This is just a wrapper around self.recv(size).
        '''

        return self.recv(size)

    def readinto(self, buf, buflen=0, flags=0):
        '''Read bytes into the buf.

        If nbytes is specified then read at most that many bytes.
        Otherwise, read at most len(buf) bytes.

        This is just a wrapper around self.recv_into(buf, ...).
        '''
        return self.recv_into(buf, buflen, flags)
