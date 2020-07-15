from unittest import TestCase

from pyDistrib import Worker, Status


class TestWorker(TestCase):

    def test_worker_goes_offline_after_two_missed_acks(self):
        worker = Worker("1.1.1.1", 1, Status.ONLINE, "1afc7e9f")
        worker.missed_ack()
        worker.missed_ack()
        assert worker.is_offline()

    def test_worker_inequality(self):
        worker1 = Worker("1.1.1.1", 1, Status.ONLINE, "1afc7e9f")
        worker2 = Worker("2.2.2.2", 1, Status.ONLINE, "1afc7e9f")
        assert worker1 != worker2

    def test_worker_equality(self):
        worker1 = Worker("1.1.1.1", 1, Status.ONLINE, "1afc7e9f")
        worker2 = Worker("1.1.1.1", 45, Status.OFFLINE, "1afc7e9f")
        assert worker1 == worker2
