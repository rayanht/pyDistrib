import logging
import socket
import time
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager

from .atomic_counter import AtomicCounter
from .worker import Worker, Status
from .udp_socket_wrapper import udp_socket

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class PyDistribServer:
    HANDSHAKE_PORT = None

    def __init__(self):
        self.workers = set()
        self.UDP_PORT = 5007
        self.counter = AtomicCounter()
        self.alive = True

    @contextmanager
    def start(self):
        with ThreadPoolExecutor() as executor:
            executor.submit(self.listen_for_handshake)
            executor.submit(self.multicast_discovery_signals)
            executor.submit(self.keep_workers_alive)
            yield self
            self.alive = False

    def multicast_discovery_signals(self):
        while self.HANDSHAKE_PORT is None:
            time.sleep(2)
        logging.info("Broadcasting discovery signals")
        with udp_socket() as sock:
            MCAST_GRP = '224.1.1.1'
            MCAST_PORT = 5007
            MULTICAST_TTL = 2
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

            while self.alive:
                sock.sendto(bytes(f"PyDistrib INIT|{self.HANDSHAKE_PORT}", "utf-8"), (MCAST_GRP, MCAST_PORT))

    def keep_workers_alive(self):
        while self.alive:
            with ThreadPoolExecutor() as executor:
                for worker in filter(Worker.is_online, self.workers):
                    executor.submit(self.keep_alive_routine, worker)
            time.sleep(10)

    def keep_alive_routine(self, worker: Worker):
        with udp_socket(binding=("", self.UDP_PORT), timeout=5) as sock:
            logging.info(f"Sending a keep alive signal to {worker}")
            sock.sendto(b'PyDistrib KEEPALIVE', (worker.address, self.UDP_PORT))
            try:
                data, addr = sock.recvfrom(1024)
                if b'PyDistrib KEEPALIVE ACK' in data:
                    uuid = str(data).split("|")[1]
                    if uuid == worker.uuid:
                        logging.info(f"{worker} acknowledged the keep alive signal")
                        return
            except socket.timeout:
                worker.missed_ack()
                return
            worker.missed_ack()

    def listen_for_handshake(self):
        with udp_socket(binding=("", 0), timeout=3) as sock:
            _, self.HANDSHAKE_PORT = sock.getsockname()
            logging.info(f"Listening for handshakes on port {self.HANDSHAKE_PORT}")
            while self.alive:
                try:
                    data, (addr, port) = sock.recvfrom(1024)
                    if b'PyDistrib HANDSHAKE' in data:
                        uuid = data.decode("utf-8").split("|")[1]
                        self.acknowledge_handshake(addr, port, uuid)
                except socket.timeout:
                    pass

    def acknowledge_handshake(self, addr, port, uuid):
        with udp_socket() as ack_socket:
            ack_socket.sendto(bytes(f"PyDistrib HANDSHAKE ACK|{uuid}", 'utf-8'), (addr, port))
        worker = Worker(addr, self.counter.get_and_increment(), Status.PENDING, uuid)
        if worker in self.workers:
            logging.debug(f"A worker with address {worker.address} and id {worker.uuid} is already registered")
            self.counter.decrement()
            return
        offline_workers = set(filter(Worker.is_offline, self.workers))
        if worker in offline_workers:
            self.counter.decrement()
            worker = next(x for x in offline_workers if x == worker)
            worker.set_status(Status.ONLINE)
            logging.info(f"Connection recovered. Worker: {worker}")
        else:
            self.workers.add(worker)
            worker.set_status(Status.ONLINE)
            logging.info(f"Connection established. New worker: {worker} with id {worker.uuid}")
