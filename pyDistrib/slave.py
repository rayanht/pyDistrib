from enum import Enum


class Status(Enum):
    OFFLINE = 0
    READY = 1
    BUSY = 2

    def __str__(self):
        return self.name


class Slave:

    def __init__(self, address: str, number: int, status: Status):
        self.status = status
        self.number = number
        self.address = address

    def __repr__(self):
        return f"Slave #{self.number} @ {self.address}. Status: {self.status}"

    def __str__(self):
        return f"Slave #{self.number} ({self.address})"
