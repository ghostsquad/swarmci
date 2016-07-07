import time
from uuid import uuid4
from swarmci.util import get_logger
from swarmci.exceptions import InvalidOperationException


class Task(object):
    def __init__(self, name):
        self.logger = get_logger(__name__)
        self.id = str(uuid4())
        self.name = name
        if self.name is None:
            raise ValueError('an identifiable object must have a name!')

        self.start = None
        self.end = None
        self.runtime = None
        self.success = None
        self.result = None

    def start(self):
        if self.start is not None:
            raise InvalidOperationException('task already started.')
        self.start = time.time()

    def stop(self):
        if self.start is None:
            raise InvalidOperationException('task cannot be stopped without being started first.')

        if self.end is not None:
            raise InvalidOperationException('task has already been stopped.')

        self.end = time.time()
        self.runtime = self.start - self.end

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()