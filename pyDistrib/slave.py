from enum import Enum

from atomic_counter import AtomicCounter


class Status(Enum):
    OFFLINE = 0
    ONLINE = 1
    BUSY = 2

    def __str__(self):
        return self.name


class Slave:

    def __init__(self, address: str, sequence_number: int, status: Status, uuid: str):
        self.status = status
        self.sequence_number = sequence_number
        self.address = address
        self.uuid = uuid
        self.counter = AtomicCounter(initial=1)
        self.lives = self.counter.get()

    def missed_ack(self):
        self.lives = self.counter.get_and_decrement()

    def is_online(self):
        return self.status == Status.ONLINE or self.status == Status.BUSY

    def is_offline(self):
        return self.status == Status.OFFLINE

    def set_status(self, status: Status):
        self.status = status

    def get_address(self):
        return self.address

    def __eq__(self, other):
        if not isinstance(other, Slave):
            return False
        return other.address == self.address and other.uuid == self.uuid

    def __repr__(self):
        return f"Slave #{self.sequence_number}/{self.uuid} @ {self.address}. Status: {self.status}"

    def __hash__(self):
        return hash((self.address, self.uuid))

    def __str__(self):
        return f"Slave #{self.sequence_number} ({self.address})"
