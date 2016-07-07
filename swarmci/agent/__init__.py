import yaml
import logging
import sys
from os import path
from swarmci.util import get_logger
from swarmci.exceptions import BuildAgentException
from swarmci.stage import Stage
from swarmci.job import Job
from swarmci.runners.strategies.stop_on_failure import stop_on_failure
from swarmci.runners.strategies.multi_threaded import run_multithreaded
from swarmci.runners import stage, job, docker_exec

logger = get_logger(__name__)


def create_stages(yaml_path):
    """

    :param yaml_path:
    :return:
    """
    logger.debug('opening %s', yaml_path)
    with open(yaml_path, 'r') as f:
        data = yaml.load(f)

    logger.debug('yaml file loaded')

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


def main():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s (%(threadName)-10s) [%(levelname)8s] - %(message)s")

    logging.getLogger('requests').setLevel(logging.WARNING)

    stages = create_stages(path.abspath('.swarmci'))

    docker_runner = docker_exec.DockerRunner(image='python:alpine')
    task_runner = docker_exec.DockerExecRunner(docker_runner=docker_runner)
    job_runner = job.JobRunner(run_all_strategy=run_multithreaded, task_runner=task_runner)
    stage_runner = stage.StageRunner(run_all_strategy=stop_on_failure, job_runner=job_runner)

    logger.debug('starting stages')
    result = stage_runner.run_all(stages)
    if result:
        logger.info('all stages completed successfully!')
    else:
        logger.error('some stages did not complete successfully. :(')

if __name__ == '__main__':
    main()
