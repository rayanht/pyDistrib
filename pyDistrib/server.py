import os
import socket
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Thread
from time import sleep

from atomic_counter import AtomicCounter
from slave import Slave, Status


class PyDistribServer:

    # TODO Replace debug print statements with proper logging

    def __init__(self):
        self.slaves = set()
        self.timed_out_slaves = set()
        self.UDP_IP = '255.255.255.255'
        # TODO We probably only need 1 port
        self.UDP_PORT1 = 6789
        self.UDP_PORT2 = 6790
        self.UDP_PORT3 = 6791
        self.counter = AtomicCounter()

    def start(self):
        Thread(target=self.listen_for_handshake).start()
        Thread(target=self.broadcast_discovery_signals).start()
        Thread(target=self.keep_slaves_alive).start()

    def broadcast_discovery_signals(self):
        with self.udp_socket() as sock:
            while True:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(b'PyDistrib INIT', (self.UDP_IP, self.UDP_PORT1))
                sleep(3)

    def keep_slaves_alive(self):
        while True:
            with ThreadPoolExecutor(max_workers=os.cpu_count() - 1) as executor:
                for slave in self.slaves:
                    executor.submit(self.keep_alive_routine, slave)
            self.slaves -= self.timed_out_slaves
            sleep(5)

    def keep_alive_routine(self, slave: Slave):
        with self.udp_socket() as sock:
            sock.bind(("", self.UDP_PORT3))
            sock.settimeout(5)
            print("Sending a keep alive signal to", slave)
            sock.sendto(b'PyDistrib KEEPALIVE', (slave.address, self.UDP_PORT3))
            try:
                data, addr = sock.recvfrom(1024)
                if data == b'PyDistrib KEEPALIVE ACK':
                    print(slave, "acknowledged the keep alive signal\n")
            except socket.timeout:
                print(slave, "timed out\n")
                self.timed_out_slaves.add(slave)

    def listen_for_handshake(self):
        with self.udp_socket() as sock:
            sock.bind(("", self.UDP_PORT2))
            while True:
                data, addr = sock.recvfrom(1024)
                if data == b'PyDistrib HANDSHAKE':
                    slave = Slave(addr[0], self.counter.get_and_increment(), Status.READY)
                    with self.udp_socket() as ack_socket:
                        ack_socket.sendto(b'PyDistrib HANDSHAKE ACK', (addr[0], self.UDP_PORT1))
                    print("Connection established. New slave:", slave)
                    self.slaves.add(slave)
                    self.timed_out_slaves.discard(slave)
                sleep(5)


    @contextmanager
    def udp_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        yield s
        s.close()
