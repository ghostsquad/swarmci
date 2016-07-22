import argparse
import logging
import os
import sys
import yaml
from os import path
from swarmci.util import get_logger
from swarmci.exceptions import BuildAgentException
from swarmci.stage import Stage
from swarmci.job import Job
from swarmci.runners.strategies.stop_on_failure import stop_on_failure
from swarmci.runners.strategies.multi_threaded import run_multithreaded
from swarmci.runners import stage, job, docker_exec

logger = get_logger(__name__)

script_version = "0.1"

here = os.path.dirname(os.path.realpath(__file__))


def create_stages(yaml_path):
    """

    :param yaml_path:
    :return:
    """
    logger.debug('opening %s', yaml_path)
    with open(yaml_path, 'r') as f:
        data = yaml.load(f)

    logger.debug('yaml file loaded')

    stages_from_yaml = data.get('stages', None)
    if stages_from_yaml is None:
        raise BuildAgentException('[stages] key not found in yaml file!')

    if type(stages_from_yaml) is not list:
        raise BuildAgentException('[stages] should be a list in the yaml file!')

    stages = []
    for _stage in stages_from_yaml:
        stage_name = list(_stage)[0]
        # each stage should be a dictionary with 1 key (the name of the stage).
        # the value should be a list of jobs.

        jobs = []
        for _job in _stage[stage_name]:
            # each job should be a dictionary with 1 key (the name of the job).
            # the value should be a dictionary containing the job details
            _job['images'] = _job.pop('images', _job.pop('image', None))
            _job['tasks'] = _job.pop('tasks', _job.pop('task', None))
            jobs.append(Job(**_job))

        stages.append(Stage(name=stage_name, jobs=jobs))

    return stages


def parse_args(args):
    """parse cmdline args and return options to caller"""
    parser = argparse.ArgumentParser(
        description="CodeBuildr - YAML-based Build Runner")

    required_args = parser.add_argument_group('required named arguments')
    required_args.add_argument('--demo', action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(script_version))

    parser.add_argument('--file', action='store', default='.swarmci')

    return parser.parse_args(args)


def main(args):
    args = parse_args(args)
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s (%(threadName)-10s) [%(levelname)8s] - %(message)s")

    if args.demo:
        swarmci_file = os.path.join(here, '../.swarmci')
    else:
        swarmci_file = args.file

    swarmci_file = os.path.abspath(swarmci_file)

    if not swarmci_file:
        msg = 'must provide either --file or --demo'
        logger.error(msg)
        raise Exception(msg)

    logging.getLogger('requests').setLevel(logging.WARNING)

    stages = create_stages(swarmci_file)

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

