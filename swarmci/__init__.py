import argparse
import logging
import os
import sys
import yaml
from os import path
from uuid import uuid4
from swarmci.util import get_logger
from swarmci.exceptions import SwarmCIException
from swarmci.task import Task, TaskType
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner

logger = get_logger(__name__)

here = path.abspath(path.dirname(__file__))

# Get version from the VERSION file
with open(path.join(here, 'VERSION'), encoding='utf-8') as f:
    version = f.readline().strip()

here = os.path.dirname(os.path.realpath(__file__))


def load_swarmci_config(yaml_path):
    logger.debug('opening %s', yaml_path)
    with open(yaml_path, 'r') as f:
        return yaml.load(f)


def build_tasks_hierarchy(swarmci_config, docker_runner=DockerRunner):
    stages_from_yaml = swarmci_config.pop('stages', None)
    if stages_from_yaml is None:
        raise SwarmCIException('Did not find "stages" key in the .swarmci file.')
    elif type(stages_from_yaml) is not list:
        raise SwarmCIException('The value of the "stages" key should be a list in the .swarmci file.')

    stage_tasks = []
    for stage in stages_from_yaml:
        job_tasks = []
        for job in stage['jobs']:

            commands = []
            for cmd in job['commands']:

                def init_command_func(_cmd):
                    def command_func(*args, **kwargs):
                        docker_runner.run_in_docker(_cmd, *args, **kwargs)
                    return command_func

                command_task = Task(cmd, TaskType.COMMAND, exec_func=init_command_func(cmd))
                commands.append(command_task)

            def init_job_func(image, _commands):
                def job_func():
                    runner = docker_runner(image)
                    runner.run_all(_commands)
                return job_func

            job_task = Task(job['name'], TaskType.JOB, exec_func=init_job_func(job['image'], commands))
            job_tasks.append(job_task)

        def init_stage_func(_job_tasks):
            def stage_func():
                runner = ThreadedRunner()
                runner.run_all(_job_tasks)
            return stage_func

        stage_task = Task(stage['name'], TaskType.STAGE, exec_func=init_stage_func(job_tasks))
        stage_tasks.append(stage_task)

    def init_build_func(_stage_tasks):
        def build_func():
            _runner = SerialRunner()
            _runner.run_all(_stage_tasks)
        return build_func

    build_task = Task(str(uuid4()), TaskType.BUILD, exec_func=init_build_func(stage_tasks))

    return build_task


def parse_args(args):
    """parse cmdline args and return options to caller"""
    parser = argparse.ArgumentParser(
        description=("SwarmCI is a CI extension leveraging Docker Swarm to"
                     "enable parallel, distributed, isolated build tasks."))

    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(version))

    parser.add_argument('--file', action='store', default='.swarmci')

    return parser.parse_args(args)


def main(args):
    args = parse_args(args)
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format="%(asctime)s (%(threadName)-10s) [%(levelname)8s] - %(message)s")

    swarmci_file = args.file if args.file else os.path.join(os.getcwd(), '.swarmci')

    swarmci_file = os.path.abspath(swarmci_file)

    if not swarmci_file:
        msg = 'must provide either --file or --demo'
        logger.error(msg)
        raise Exception(msg)

    logging.getLogger('requests').setLevel(logging.WARNING)

    swarmci_config = load_swarmci_config(swarmci_file)
    build_task = build_tasks_hierarchy(swarmci_config)

    logger.debug('starting build')
    build_task.execute()
    if build_task.successful:
        logger.info('all stages completed successfully!')
    else:
        logger.error('some stages did not complete successfully. :(')
