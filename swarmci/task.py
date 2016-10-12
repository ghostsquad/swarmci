import sys
import traceback
import time
from uuid import uuid4
from swarmci.util import get_logger, raise_
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner


class Task(object):
    def __init__(self, name, sub_tasks=None, tm=None):
        self.logger = get_logger(__name__)
        self.id = str(uuid4())
        self._tm = time.time if tm is None else tm

        self._name = name or raise_(ValueError('tasks must have a name'))

        self._task_type_pretty = str(self.__class__.__name__).lower().capitalize()[0:-4]

        self._subtasks = sub_tasks if sub_tasks else []

        self.start_time = None
        self.end_time = None
        self._runtime = None
        self._successful = False
        self._results = []
        self._exc_info = None

    @property
    def name(self):
        return self._name

    @property
    def successful(self):
        return self._successful

    @property
    def task_type_pretty(self):
        return self._task_type_pretty

    @property
    def subtasks(self):
        return self._subtasks

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    @property
    def exc_info(self):
        return self._exc_info

    @property
    def runtime(self):
        return self._runtime

    @property
    def runtime_str(self):
        if self._runtime is None:
            return 'N/A'
        minutes, seconds = divmod(self._runtime, 60.0)
        return '{} min {:.2f} sec'.format(int(minutes), seconds)

    def _execute(self, *args, **kwargs):
        raise NotImplementedError

    def execute(self, *args, **kwargs):
        end_msg_fmt = '{} Ended {} - {}'

        self.start_time = self._tm()
        self.logger.info('Starting %s - %s', self._task_type_pretty, self.name)
        try:
            self.results = self._execute(*args, **kwargs)
            self._successful = True
            self.logger.info(end_msg_fmt.format(self._task_type_pretty, "successfully", self.name))
        except Exception:
            self._successful = False
            self._exc_info = sys.exc_info()
            self.logger.debug(traceback.format_exc())
            result_msg = end_msg_fmt.format(self._task_type_pretty, "with an error", self.name)
            self.logger.error(result_msg)
        finally:
            self.end_time = self._tm()
            self._runtime = self.end_time - self.start_time
            self.logger.info('%s Runtime - %s', self._task_type_pretty, self.runtime_str)


class RunnerTask(Task):
    def __init__(self, name, runner, *args, **kwargs):
        self._runner = runner
        super().__init__(name, *args, **kwargs)

    def _execute(self, *args, **kwargs):
        self._runner.run_all(self.subtasks)


class BuildTask(RunnerTask):
    """
    A Build Task runs Stages, which run serially
    """

    def __init__(self, name, runner=None, *args, **kwargs):
        if runner is None:
            runner = SerialRunner()
        super().__init__(name, runner, *args, **kwargs)


class StageTask(RunnerTask):
    """
    A Stage Task runs jobs, which run in parallel
    """

    def __init__(self, name, runner=None, thread_pool_executor=None, *args, **kwargs):
        if runner is None:
            if thread_pool_executor is None:
                raise ValueError("thread_pool_executor is required if runner is not provided")
            runner = ThreadedRunner(thread_pool_executor)
        super().__init__(name, runner, *args, **kwargs)


class JobTask(RunnerTask):
    """
    A Job Task runs commands, which run serially
    """

    def __init__(self, name, runner=None, image=None, *args, **kwargs):
        if runner is None:
            if image is None:
                raise ValueError("image is required if runner is not provided")
            runner = DockerRunner(image)
        super().__init__(name, runner, *args, **kwargs)


class CommandTask(Task):
    def __init__(self, name, *args, docker_run=None, **kwargs):
        self._docker_run = docker_run if docker_run else DockerRunner.run_in_docker
        super().__init__(name, *args, **kwargs)

    def _execute(self, *args, **kwargs):
        self._docker_run(self.name, out_func=self.results.append, *args, **kwargs)
