import yaml
import asyncio
from docker import Client
from queue import Queue
from swarmci.util import get_logger
from swarmci.exceptions import BuildAgentException
from swarmci import Stage, Job
from swarmci.agent.job_worker import JobWorker

logger = get_logger(__name__)


def create_stages(yaml_path):
    """

    :param yaml_path:
    :return:
    """
    with open(yaml_path, 'r') as f:
        data = yaml.load(f)

    _stages = data.get('stages', None)
    if _stages is None:
        raise BuildAgentException('[stages] key not found in yaml file!')

    if type(_stages) is not list:
        raise BuildAgentException('[stages] should be a list in the yaml file!')

    stages = []
    for _stage in _stages:
        stage_name = list(_stage)[0]

        jobs = []
        for job_name, _job in _stage[stage_name].items():
            f = _job.pop('finally', None)
            if f is not None:
                _job['finally_task'] = f

            job = Job(
                images=_job.pop('images', _job.pop('image', None)),
                tasks=_job.pop('tasks', _job.pop('task', None)),
                name=job_name,
                **_job
            )

            jobs.append(job)

        st = Stage(name=stage_name, jobs=jobs)
        stages.append(st)

    return stages


def run_job(job):
    """
    Running a job means to
    1. run a docker image in the swarm
    3. wait for job event specifying that the container has started, noting what node
    4. exec all tasks of the job within the container
    5. stop task execution if any* task fails
    :return: bool
    """
    raise NotImplementedError


def run_stage(stage, run_job_func=run_job, max_workers=None):
    """
    Given a number of jobs, we want to run all jobs asynchronously.
    Our return value should be true if all jobs succeed
    or false if any job fails.
    :param max_workers: defaults to number of jobs in the stage
    :param stage:
    :param run_job_func:
    :return: bool
    """

    if max_workers is None:
        max_workers = len(stage.jobs)

    queue = Queue()
    # Create worker threads
    for x in range(max_workers):
        worker = JobWorker(queue, run_job_func)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
    # Put the tasks into the queue
    for job in stage.jobs:
        logger.info('Queueing {name} ({id})'.format(name=job.name, id=job.id))
        queue.put(job)
    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()

    for job in stage.jobs:
        if not job.result:
            return False

    return True


def run_stages(stages, run_stage_func=run_stage):
    """

    :param stages:
    :param run_stage_func:
    """
    run = True

    for stage in stages:
        logger.info('running stage %s', stage.name)
        if run:
            result = run_stage_func(stage.jobs)
            if not result:
                logger.info('stage %s failed! skipping subsequent stages...', stage.name)
                run = False
        else:
            logger.info('skipping stage %s, previous stage failed', stage.name)
