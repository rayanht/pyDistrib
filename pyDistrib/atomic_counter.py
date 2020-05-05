import threading


class AtomicCounter:
    def __init__(self, initial=0):
        self.value = initial
        self._lock = threading.Lock()

    def decrement(self):
        with self._lock:
            self.value -= 1

    def get_and_increment(self):
        with self._lock:
            self.value += 1
            return self.value

    def get(self):
        with self._lock:
            return self.value

    def get_and_decrement(self):
        with self._lock:
            self.value -= 1
            return self.value
