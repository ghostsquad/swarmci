import sys
import argparse
import logging
import os
import yaml
import colorlog
from concurrent.futures import ThreadPoolExecutor
from swarmci.util import get_logger, print_task_results
from swarmci.errors import SwarmCIError
from swarmci.task import TaskType, TaskFactory
from swarmci.version import __version__

logger = get_logger(__name__)


def build_tasks_hierarchy(swarmci_config, task_factory):
    stages_from_yaml = swarmci_config.pop('stages', None)
    if stages_from_yaml is None:
        raise SwarmCIError('Did not find "stages" key in the .swarmci file.')
    elif type(stages_from_yaml) is not list:
        raise SwarmCIError('The value of the "stages" key should be a list in the .swarmci file.')

    thread_pool_executor = ThreadPoolExecutor(max_workers=25)

    stage_tasks = []
    for stage in stages_from_yaml:
        job_tasks = []
        for job in stage['jobs']:
            commands = []
            for cmd in job['commands']:
                commands.append(task_factory.create(TaskType.COMMAND, cmd=cmd))

            job_tasks.append(task_factory.create(TaskType.JOB, job=job, commands=commands))

        stage_tasks.append(
            task_factory.create(TaskType.STAGE, stage=stage, jobs=job_tasks, thread_pool_executor=thread_pool_executor))

    return task_factory.create(TaskType.BUILD, stages=stage_tasks)


def parse_args(args):
    """parse cmdline args and return options to caller"""
    parser = argparse.ArgumentParser(
        description=("SwarmCI is a CI extension leveraging Docker Swarm to"
                     "enable parallel, distributed, isolated build tasks."))

    parser.add_argument('--version', action='version',
                        version='SwarmCI {}'.format(__version__))

    parser.add_argument('--file', action='store', default='.swarmci')

    parser.add_argument('--debug', action='store_true')

    return parser.parse_args(args)


def main(args):
    args = parse_args(args)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    handler = colorlog.StreamHandler()

    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s (%(threadName)-10s) [%(levelname)8s] - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
    ))

    logger.addHandler(handler)

    swarmci_file = args.file if args.file else os.path.join(os.getcwd(), '.swarmci')

    swarmci_file = os.path.abspath(swarmci_file)

    if not swarmci_file:
        msg = 'must provide either --file or --demo'
        logger.error(msg)
        raise Exception(msg)

    logging.getLogger('requests').setLevel(logging.WARNING)

    logger.debug('opening %s', swarmci_file)
    with open(swarmci_file, 'r') as f:
        swarmci_config = yaml.load(f)

    build_task = build_tasks_hierarchy(swarmci_config, TaskFactory())

    logger.debug('starting build')
    build_task.execute()

    if build_task.successful:
        logger.info('all stages completed successfully!')
    else:
        logger.error('some stages did not complete successfully. :(')

    print_task_results(build_task)

    if not build_task.successful:
        sys.exit(1)

