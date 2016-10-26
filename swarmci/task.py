import sys
import traceback
import time
from uuid import uuid4
from swarmci.util import get_logger, raise_
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner
from swarmci.errors import TaskFailedError


class Task(object):
    """
    An arbitrary unit of work
    """

    def __init__(self, name, sub_tasks=None, tm=None):
        self.logger = get_logger(__name__)
        self.id = str(uuid4())
        self._tm = time.time if tm is None else tm

        self._name = name or raise_(ValueError('tasks must have a name'))

        self._subtasks = sub_tasks if sub_tasks else []

        self.start_time = None
        self.end_time = None
        self._runtime = None
        self._successful = False
        self._results = []
        self._exc_info = None

    @property
    def name(self):
        """
        The friendly name of the task
        :return: bool
        """
        return self._name

    @property
    def successful(self):
        """
        Whether or not the task completed without seeing an exception raised
        :return: bool
        """
        return self._successful

    @property
    def subtasks(self):
        """
        A list of child Task objects
        :return: list of Task
        """
        return self._subtasks

    @property
    def results(self):
        """
        This could be anything, in theory
        In practice, it should be a list of str
        with the stdout/error of the task
        :return: object
        """
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    @property
    def exc_info(self):
        """
        The Exception Info if the task failed
        https://docs.python.org/3/library/sys.html#sys.exc_info
        :return: 3-tuple
        """
        return self._exc_info

    @property
    def runtime(self):
        """
        Float of seconds the task took to execute
        :return: float
        """
        return self._runtime

    @property
    def runtime_str(self):
        """
        Nicely formatted runtime
        Example:

        1 min 3.02 sec

        :return: str
        """
        if self._runtime is None:
            return 'N/A'
        minutes, seconds = divmod(self._runtime, 60.0)
        return '{} min {:.2f} sec'.format(int(minutes), seconds)

    def _execute(self, *args, **kwargs):
        raise NotImplementedError

    def execute(self, *args, **kwargs):
        """
        A wrapper around the private, abstract _execute method
        Records runtime, exc_info if raised, success
        :param args: passed thru to _execute
        :param kwargs: passed thru to _execute
        """
        end_msg_fmt = '{} Ended {} - {}'

        task_type = self.__class__.__name__

        self.start_time = self._tm()
        self.logger.info('Starting %s - %s', task_type, self.name)
        try:
            self.results = self._execute(*args, **kwargs)
            self._successful = True
            self.logger.info(end_msg_fmt.format(task_type, "successfully", self.name))
        except TaskFailedError:
            self._successful = False
            self._exc_info = sys.exc_info()
            self.logger.debug(traceback.format_exc())
            result_msg = end_msg_fmt.format(task_type, "with an error", self.name)
            self.logger.error(result_msg)
        finally:
            self.end_time = self._tm()
            self._runtime = self.end_time - self.start_time
            self.logger.info('%s Runtime - %s', task_type, self.runtime_str)


class RunnerTask(Task):
    """
    A Task which runs subtasks using a Runner implementation
    """

    def __init__(self, name, runner, *args, **kwargs):
        self._runner = runner
        super().__init__(name, *args, **kwargs)

    def _execute(self, *args, **kwargs):
        self._runner.run_all(self.subtasks)


class Build(RunnerTask):
    """
    A Build runs Stages, which run serially
    """

    def __init__(self, name, runner=None, *args, **kwargs):
        if runner is None:
            runner = SerialRunner()
        super().__init__(name, runner, *args, **kwargs)


class Stage(RunnerTask):
    """
    A Stage runs jobs, which run in parallel
    """

    def __init__(self, name, runner=None, thread_pool_executor=None, *args, **kwargs):
        if runner is None:
            if thread_pool_executor is None:
                raise ValueError("thread_pool_executor is required if runner is not provided")
            runner = ThreadedRunner(thread_pool_executor)
        super().__init__(name, runner, *args, **kwargs)


class Job(RunnerTask):
    """
    A Job runs commands, which run serially
    """

    def __init__(self, name, runner=None, image=None, *args, **kwargs):
        if runner is None:
            if image is None:
                raise ValueError("image is required if runner is not provided")
            runner = DockerRunner(image)
        super().__init__(name, runner, *args, **kwargs)


class Command(Task):
    """
    A command run within a container
    """

    def __init__(self, name, *args, docker_run=None, **kwargs):
        self._docker_run = docker_run if docker_run else DockerRunner.run_in_docker
        super().__init__(name, *args, **kwargs)

    def _execute(self, *args, **kwargs):
        self._docker_run(self.name, out_func=self.results.append, *args, **kwargs)
