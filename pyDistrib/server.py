import logging
import socket
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager

from .atomic_counter import AtomicCounter
from .slave import Slave, Status
from .udp_socket_wrapper import udp_socket

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class PyDistribServer:

    def __init__(self, broadcast_port: int):
        self.slaves = set()
        self.BROADCAST_IP = '255.255.255.255'
        # TODO We probably only need 1 port
        self.BROADCAST_PORT = broadcast_port
        self.HANDSHAKE_PORT = 6790
        self.UDP_PORT3 = 6791
        self.counter = AtomicCounter()
        self.alive = True
        self.address = socket.gethostbyname(socket.gethostname())

    @contextmanager
    def start(self):
        with ThreadPoolExecutor() as executor:
            executor.submit(self.listen_for_handshake)
            executor.submit(self.broadcast_discovery_signals)
            executor.submit(self.keep_slaves_alive)
            yield self
            self.alive = False

    def broadcast_discovery_signals(self):
        with udp_socket() as sock:
            while self.alive:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(b'PyDistrib INIT', (self.BROADCAST_IP, self.BROADCAST_PORT))

    def keep_slaves_alive(self):
        while self.alive:
            with ThreadPoolExecutor() as executor:
                for slave in filter(Slave.is_online, self.slaves):
                    executor.submit(self.keep_alive_routine, slave)

    def keep_alive_routine(self, slave: Slave):
        with udp_socket(binding=("", self.UDP_PORT3), timeout=5) as sock:
            logging.info(f"Sending a keep alive signal to {slave}")
            sock.sendto(b'PyDistrib KEEPALIVE', (slave.address, self.UDP_PORT3))
            try:
                data, addr = sock.recvfrom(1024)
                if data == b'PyDistrib KEEPALIVE ACK':
                    logging.info(f"{slave} acknowledged the keep alive signal\n")
            except socket.timeout:
                slave.missed_ack()

    def listen_for_handshake(self):
        with udp_socket(binding=("", self.HANDSHAKE_PORT), timeout=3) as sock:
            while self.alive:
                try:
                    data, (addr, port) = sock.recvfrom(1024)
                    if b'PyDistrib HANDSHAKE' in data:
                        uuid = str(data).split("|")[1]
                        self.acknowledge_handshake(addr, uuid)
                except socket.timeout:
                    pass

    def acknowledge_handshake(self, addr, uuid):
        with udp_socket() as ack_socket:
            ack_socket.sendto(bytes(f"PyDistrib HANDSHAKE ACK|{uuid}", 'utf-8'), (addr, self.BROADCAST_PORT))
        slave = Slave(addr, self.counter.get_and_increment(), Status.ONLINE, uuid)
        offline_slaves = set(filter(Slave.is_offline, self.slaves))
        if slave in offline_slaves:
            self.counter.decrement()
            slave = next(x for x in offline_slaves if x == slave)
            slave.set_status(Status.ONLINE)
            logging.info(f"Connection recovered. Slave: {slave}")
        else:
            logging.info(f"Connection established. New slave: {slave}")
            self.slaves.add(slave)
