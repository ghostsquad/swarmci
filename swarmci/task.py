import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from colored import fg, attr

from swarmci.errors import TaskFailedError
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner
from swarmci.util import get_logger, raise_


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
        if docker_run:
            self._docker_run = docker_run
        else:
            self._docker_run = DockerRunner.run_in_docker
        super().__init__(name, *args, **kwargs)

    def _execute(self, *args, **kwargs):
        results = []
        self._docker_run(self.name, out_func=results.append, *args, **kwargs)
        return results

# task factory methods


def build_command_tasks(job):
    """
    Builds Command tasks from the job dict found in the .swarmci file
    :param job: dict
    :return: list of swarmci.task.Command
    """
    return map(lambda x: Command(x), job['commands'])


def build_job_tasks(stage):
    """
    Builds Job tasks from the stage dict found in the .swarmci file
    :param stage: dict
    :return: list of swarmci.task.Job
    """
    def create_job_task(job):
        commands = build_command_tasks(job)
        return Job(job['name'], image=job['image'], sub_tasks=commands)

    return map(create_job_task, stage['jobs'])


def build_stage_tasks(stages, thread_pool_executor):
    """
    Builds Stage tasks from a list of stage dicts found in the .swarmci file
    :param stages: list of dict
    :param thread_pool_executor: ThreadPoolExecutor
    :return: list of swarmci.task.Stage
    """
    def create_stage_task(stage):
        jobs = build_job_tasks(stage)
        return Stage(stage['name'], thread_pool_executor=thread_pool_executor, sub_tasks=jobs)

    return map(create_stage_task, stages)


def build_tasks_hierarchy(swarmci_config):
    """
    Builds the tasks hierarchy Build > Stages > Jobs > Commands
    :param swarmci_config: dict
    :return: swarmci.task.Build
    """
    stage_tasks = build_stage_tasks(swarmci_config['stages'], ThreadPoolExecutor(max_workers=25))

    return Build(str(uuid4()), sub_tasks=stage_tasks)

# task results


def get_command_results(task):
    yield fg(1) + task.name + attr(0)
    yield "{}----------------------------------------------{}\n".format(fg(1), attr(0))

    output_found = False

    if task.exc_info is not None:  # pragma: no cover
        # trim the last character because it's a newline
        # https://docs.python.org/2/library/traceback.html#traceback.format_exception
        for line in map(lambda x: x[0:-1], traceback.format_exception(*task.exc_info)):
            yield line
        output_found = True

    if task.results is not None and len(task.results) > 0:
        for line in task.results:
            yield line
        output_found = True

    if not output_found:
        yield '*** no output found! ***'


def decide_task_result_action(task, get_results_action):
    """
    If the task is a command, was not successful and was not skipped
    returns the get_results func (that was passed in)
    otherwise, returns a default lambda which returns an empty array
    :param task: swarmci.task.Task
    :param get_results_action: func(task)
    :return: lambda task: ...
    """
    if isinstance(task, Command) and not task.successful and task.runtime is not None:
        return get_results_action

    return lambda x: []


def decide_command_result_action(task, success, failed, skipped):
    if task.successful:
        return success

    if task.runtime is None:
        return skipped

    return failed


result_meta = {
    'successful': (fg(2), "\u2713"),
    'failed': (fg(1), "\u2717"),
    'skipped': (fg(33), "\u2933")
}


def get_final_status(results):
    success_ct = results['successful']
    failed_ct = results['failed']
    skipped_ct = results['skipped']

    def format_final_status_msg(result, count):
        color, sym = result_meta[result]
        return "{}{} {} {}".format(color, sym, count, result, attr(0)) if count > 0 else ''

    success_msg = format_final_status_msg('successful', success_ct)

    if failed_ct > 0:
        skipped_msg = format_final_status_msg('skipped', skipped_ct)
        failed_msg = format_final_status_msg('failed', failed_ct)

        return " ".join([failed_msg, skipped_msg, success_msg])

    return success_msg


def get_task_results(tasks, indent=2):
    """
    Generates
    :param tasks:
    :param indent:
    :return:
    """
    results = {
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }
    lines = []

    def incr_result(result):
        results[result] += 1
        return result_meta[result]

    for task in tasks:
        action = decide_command_result_action(task,
                                              success=lambda: incr_result('successful'),
                                              failed=lambda: incr_result('failed'),
                                              skipped=lambda: incr_result('skipped'))

        color, sym = action()

        left_pad = " " * indent
        line = "{}{}{}{} {} ({})".format(left_pad, color, sym, attr(0), task.name, task.runtime_str)
        lines.append(line)

        new_results, new_lines = get_task_results(task.subtasks, indent=indent + 2)
        for k, v in new_results.items():
            results[k] += v

        lines += new_lines

    return results, lines
