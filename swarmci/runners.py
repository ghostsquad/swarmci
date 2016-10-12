from docker import Client as DockerClient
import concurrent.futures
from swarmci.util import get_logger
from swarmci.docker import Container
from swarmci.errors import TaskFailedError

logger = get_logger(__name__)


class RunnerBase(object):
    def __init__(self):
        self.tasks = []
        self.logger = get_logger(__name__)

    @staticmethod
    def run(task, *args, **kwargs):
        task.execute(*args, **kwargs)
        return task.successful

    def run_all(self, tasks):
        raise NotImplementedError

    def raise_if_not_successful(self, task):
        if not task.successful:
            msg = "Failure detected, skipping further %ss" % task.task_type_pretty
            self.logger.error(msg)
            raise TaskFailedError(msg)


class SerialRunner(RunnerBase):
    """
    Serial is responsible for running all tasks serially.
    It should only progress to the next task if the previous task completed successfully.
    """

    def run_all(self, tasks):
        self.tasks = []
        for task in tasks:
            self.run(task)
            self.raise_if_not_successful(task)


class ThreadedRunner(RunnerBase):
    """
    Threaded is responsible for running all tasks in parallel (threads).
    Success should be set to true only if all tasks were successful.
    """

    def __init__(self, thread_pool_executor):
        self._thread_pool_executor = thread_pool_executor
        super().__init__()

    def run_all(self, tasks):
        futures = list(map(lambda t: self._thread_pool_executor.submit(self.run, t), tasks))
        concurrent.futures.wait(futures)

        if not all(t.successful for t in tasks):
            msg = "Failure detected in one or more {}s!".format(tasks[0].task_type_pretty)
            self.logger.error(msg)
            raise TaskFailedError(msg)


class DockerRunner(RunnerBase):
    """
    DockerRunner is responsible for running tasks within a Docker Container.
    It is similar to the SerialRunner, in that it also runs tasks serially, and quits if a task fails.
    """

    def __init__(self, image, remove=True, url=':4000', env=None, docker=None, cn=None, **kwargs):
        self.docker = docker or DockerClient(base_url=url, version='1.24')
        self.image = image
        self.remove = remove
        self.env = env or {}
        self._cn = cn or Container

        kwargs.setdefault('binds', [])
        kwargs.setdefault('network_mode', 'bridge')

        self.host_config = self.docker.create_host_config(**kwargs)
        self.id = None

        super().__init__()

    @staticmethod
    def run_in_docker(command, cn, out_func=None):
        cn.execute(command, out_func=out_func)

    def run_all(self, tasks):
        with self._cn(self.image, self.host_config, self.docker, env=self.env) as cn:
            self.logger.info('Using Container %s', cn.id[0:11])
            for task in tasks:
                self.run(task, cn=cn)
                self.raise_if_not_successful(task)
