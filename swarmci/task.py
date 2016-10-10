import time
from uuid import uuid4
from enum import Enum
from swarmci.util import get_logger, raise_
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner


class TaskType(Enum):
    BUILD = 1
    STAGE = 2
    JOB = 3
    COMMAND = 4


class Task(object):
    def __init__(self, name, task_type, exec_func, sub_tasks=None, tm=None):
        self.logger = get_logger(__name__)
        self.id = str(uuid4())
        self._tm = time.time if tm is None else tm

        self._name = name or raise_(ValueError('tasks must have a name'))

        if type(task_type) is not TaskType:
            raise ValueError('task_type must be of type TaskType')

        self._task_type = task_type

        self.exec_func = exec_func if callable(exec_func) else raise_(ValueError('exec_func must be a callable'))

        self._task_type_pretty = str(self.task_type.name).lower().capitalize()

        self._subtasks = sub_tasks if sub_tasks else []

        self.start_time = None
        self.end_time = None
        self._runtime = None
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
    def error(self):
        return self._error

    @property
    def runtime(self):
        return self._runtime

    @property
    def runtime_str(self):
        if self._runtime is None:
            return 'N/A'
        minutes, seconds = divmod(self._runtime, 60.0)
        return '{} min {:.2f} sec'.format(int(minutes), seconds)

    def execute(self, *args, **kwargs):
        end_msg_fmt = '{} Ended {} - {}'

        self.start_time = self._tm()
        self.logger.info('Starting %s - %s', self._task_type_pretty, self.name)
        try:
            self.results = self.exec_func(*args, **kwargs)
            self._successful = True
            self.logger.info(end_msg_fmt.format(self._task_type_pretty, "successfully", self.name))
        except Exception as exc:
            self._successful = False
            self._error = exc
            result_msg = end_msg_fmt.format(self._task_type_pretty, "with an error", self.name)
            self.logger.error(result_msg)
        finally:
            self.end_time = self._tm()
            self._runtime = self.end_time - self.start_time
            self.logger.info('%s Runtime - %s', self._task_type_pretty, self.runtime_str)


class TaskFactory(object):
    def __init__(self, runners=None):
        self.runners = {
            'job': DockerRunner,
            'stage': ThreadedRunner,
            'build': SerialRunner
        }

        if runners:
            self.runners.update(runners)

    def create(self, task_type, *args, **kwargs):
        switcher = {
            TaskType.COMMAND: self.create_command_task,
            TaskType.JOB: self.create_job_task,
            TaskType.STAGE: self.create_stage_task,
            TaskType.BUILD: self.create_build_task
        }

        func = switcher.get(task_type, lambda: raise_(ValueError("Unknown task_type {}".format(task_type))))
        return func(*args, **kwargs)

    @staticmethod
    def create_command_task(cmd, run_func=DockerRunner.run_in_docker):
        def command_func(*args, **kwargs):
            return run_func(cmd, *args, **kwargs)

        return Task(cmd, TaskType.COMMAND, exec_func=command_func)

    def create_job_task(self, job, commands):
        runner = self.runners['job']

        def job_func():
            return runner(job['image']).run_all(commands)

        return Task(job['name'], TaskType.JOB, sub_tasks=commands, exec_func=job_func)

    def create_stage_task(self, stage, jobs, thread_pool_executor):
        runner = self.runners['stage']

        def stage_func():
            return runner(thread_pool_executor).run_all(jobs)

        return Task(stage['name'], TaskType.STAGE, sub_tasks=jobs, exec_func=stage_func)

    def create_build_task(self, stages):
        runner = self.runners['build']

        def build_func():
            return runner().run_all(stages)

        return Task(str(uuid4()), TaskType.BUILD, sub_tasks=stages, exec_func=build_func)
