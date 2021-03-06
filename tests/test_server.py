import socket
import unittest

from pyDistrib import PyDistribServer
from pyDistrib import udp_socket

TEST_PORT = 9999


class TestServer(unittest.TestCase):

    def test_server_is_broadcasting(self):
        with PyDistribServer(TEST_PORT).start():
            with udp_socket(binding=("", TEST_PORT), timeout=10) as sock:
                try:
                    data, _ = sock.recvfrom(1024)
                    if data == b'PyDistrib INIT':
                        assert True
                except socket.timeout:
                    self.fail("Socket timed out")

    def test_server_handshake(self):
        uid = "593a553c-9004-11ea-bc55-0242ac130003"
        with PyDistribServer(TEST_PORT).start() as server:
            with udp_socket(binding=("", TEST_PORT), timeout=10) as sock:
                try:
                    data, (addr, port) = sock.recvfrom(1024)
                    if data == b'PyDistrib INIT':
                        sock.sendto(bytes(f"PyDistrib HANDSHAKE|{uid}", 'utf-8'), (addr, server.HANDSHAKE_PORT))
                        try:
                            data, host = sock.recvfrom(1024)
                            if b'PyDistrib HANDSHAKE ACK' in data:
                                returned_uid = str(data).split("|")[1]
                                assert uid == returned_uid
                        except socket.timeout:
                            self.fail("Socket timed out")
                except socket.timeout:
                    server.shutdown()
                    self.fail("Socket timed out")
