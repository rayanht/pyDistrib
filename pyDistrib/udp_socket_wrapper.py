import socket
from contextlib import contextmanager


@contextmanager
def udp_socket(binding=None, timeout=0) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    if binding:
        s.bind(binding)
    yield s
    s.close()
