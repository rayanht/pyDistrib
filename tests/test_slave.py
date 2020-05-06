from unittest import TestCase

from pyDistrib import Slave, Status


class TestSlave(TestCase):

    def test_slave_goes_offline_after_two_missed_acks(self):
        slave = Slave("1.1.1.1", 1, Status.ONLINE, "1afc7e9f")
        slave.missed_ack()
        slave.missed_ack()
        assert slave.is_offline()

    def test_slave_inequality(self):
        slave1 = Slave("1.1.1.1", 1, Status.ONLINE, "1afc7e9f")
        slave2 = Slave("2.2.2.2", 1, Status.ONLINE, "1afc7e9f")
        assert slave1 != slave2

    def test_slave_equality(self):
        slave1 = Slave("1.1.1.1", 1, Status.ONLINE, "1afc7e9f")
        slave2 = Slave("1.1.1.1", 45, Status.OFFLINE, "1afc7e9f")
        assert slave1 == slave2
