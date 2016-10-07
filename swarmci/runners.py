from docker import Client as DockerClient
from swarmci.util import get_logger
from swarmci.docker import Container

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


class SerialRunner(RunnerBase):
    """
    Serial is responsible for running all tasks serially.
    It should only progress to the next task if the previous stage completed successfully.
    """

    def run_all(self, tasks):
        self.tasks = []
        for task in tasks:
            result = self.run(task)
            if not result:
                self.logger.error('failure detected, skipping further %ss', task.task_type)
                return False

        return True


class ThreadedRunner(RunnerBase):
    """
    Threaded is responsible for running all tasks in parallel (threads).
    Success should be set to true only if all tasks were successful.
    """

    def __init__(self, thread_pool_executor):
        self._thread_pool_executor = thread_pool_executor
        super().__init__()

    def run_all(self, tasks):
        results = self._thread_pool_executor.map(self.run, tasks)
        if all(results):
            return True

        return False


class DockerRunner(RunnerBase):
    """
    DockerRunner is responsible for running tasks within a Docker Container.
    Tasks that return exit code 0 should be marked successful.
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
    def run_in_docker(command, cn):
        logger.info("----BEGIN STDOUT----")
        cn.execute(command)
        logger.info("----END STDOUT----")

    def run_all(self, tasks):
        with self._cn(self.image, self.host_config, self.docker, env=self.env) as cn:
            self.logger.info('Using Container %s', cn.id[0:11])
            for task in tasks:
                result = self.run(task, cn=cn)
                if not result:
                    self.logger.error('Failure detected! skipping further %ss', task.pretty_task_type)
                    return False
            return True
