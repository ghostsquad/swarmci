import time
from uuid import uuid4
from swarmci.util import get_logger, raise_
from enum import Enum


class TaskType(Enum):
    BUILD = 1
    STAGE = 2
    JOB = 3
    COMMAND = 4


class Task(object):
    def __init__(self, name, task_type, exec_func, tm=None):
        self.logger = get_logger(__name__)
        self.id = str(uuid4())
        self._tm = time.time if tm is None else tm

        self._name = name or raise_(ValueError('tasks must have a name'))

        if type(task_type) is not TaskType:
            raise ValueError('task_type must be of type TaskType')

        self._task_type = task_type

        self.exec_func = exec_func if callable(exec_func) else raise_(ValueError('exec_func must be a callable'))

        self._task_type_pretty = str(self.task_type.name).lower().capitalize()

        self.start_time = None
        self.end_time = None
        self.runtime = None
        self._successful = False
        self._results = None
        self._error = None

    @property
    def name(self):
        return self._name

    @property
    def successful(self):
        return self._successful

    @property
    def task_type(self):
        return self._task_type

    @property
    def pretty_task_type(self):
        return self._task_type_pretty

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    @property
    def error(self):
        return self._error

    def execute(self, *args, **kwargs):
        end_msg_fmt = '{} Ended {} - {}'

        self.start_time = self._tm()
        self.logger.info('Starting %s - %s', self._task_type_pretty, self.name)
        try:
            self.results = self.exec_func(*args, **kwargs)
            self._successful = True
            self.logger.info(end_msg_fmt.format(self._task_type_pretty, "successfully", self.name))
        except Exception as exc:
            self._error = exc
            result_msg = end_msg_fmt.format(self._task_type_pretty, "with an error", self.name)
            self.logger.exception(result_msg, exc_info=exc)
        finally:
            self.end_time = self._tm()
            self.runtime = self.end_time - self.start_time
            minutes, seconds = divmod(self.runtime, 60.0)
            self.logger.info('%s Runtime - %s min %.2f sec', self._task_type_pretty, int(minutes), seconds)
