import socket
from threading import Thread
from time import sleep


class PyDistribServer:

    # TODO Replace debug print statements with proper logging

    def __init__(self):
        self.sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.slaves = set()
        # TODO Get broadcast address from the NIC
        self.UDP_IP = '255.255.255.255'
        self.UDP_PORT1 = 6789
        self.UDP_PORT2 = 6790

    def start(self):

        Thread(target=controller.listen_for_handshake, args=(self.sock1,)).start()
        Thread(target=controller.broadcast_recon, args=(self.sock2,)).start()

    def broadcast_recon(self, sock):
        while True:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(b'PyDistrib INIT', (self.UDP_IP, self.UDP_PORT1))
            sleep(5)

    def listen_for_handshake(self, sock):
        sock.bind(("", self.UDP_PORT2))
        sock.settimeout(5)
        while True:
            print("Slaves:", self.slaves)
            try:
                data, addr = sock.recvfrom(1024)
                if data == b'PyDistrib HANDSHAKE':
                    ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    ack_socket.sendto(b'PyDistrib HANDSHAKE ACK', (addr[0], self.UDP_PORT1))
                    self.slaves.add(addr)
                sleep(5)
            except socket.timeout:
                pass
            finally:
                timed_out_slaves = set()
                for slave in self.slaves:
                    print("SENDING KEEPALIVE TO", slave)
                    sock.sendto(b'PyDistrib KEEPALIVE', slave)
                    try:
                        data, addr = sock.recvfrom(1024)
                        if data == b'PyDistrib KEEPALIVE ACK':
                            print(addr, "KEEPALIVE ACK")
                    except socket.timeout:
                        print(slave, "timed out")
                        timed_out_slaves.add(slave)
                self.slaves -= timed_out_slaves
                sleep(5)