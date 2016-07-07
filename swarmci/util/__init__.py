import logging
from functools import wraps


def get_logger(name):
    """creates a logger with NullHandler"""
    _logger = logging.getLogger(name)
    _logger.addHandler(logging.NullHandler())
    return _logger


def synchronized(tlockname):
    """A decorator to place an instance based lock around a method """
    def _synched(func):
        @wraps(func)
        def _synchronizer(self,*args, **kwargs):
            tlock = self.__getattribute__(tlockname)
            tlock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                tlock.release()
        return _synchronizer
    return _synched
