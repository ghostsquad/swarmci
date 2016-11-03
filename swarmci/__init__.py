# coding=utf-8
import argparse
import logging
import os
import sys

import jsonschema

import colorlog
import yaml

from swarmci.task import build_tasks_hierarchy, get_task_results
from swarmci.util import get_logger
from swarmci.version import __version__
from swarmci.swarmci_schema import SCHEMA

logger = get_logger(__name__)


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
    # handle args
    args = parse_args(args)

    # setup logging
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

    logging.getLogger('requests').setLevel(logging.WARNING)

    # load swarmci file
    swarmci_file = args.file if args.file else os.path.join(os.getcwd(), '.swarmci')

    swarmci_file = os.path.abspath(swarmci_file)

    if not swarmci_file:
        msg = 'must provide either --file or --demo'
        logger.error(msg)
        raise Exception(msg)

    logger.debug('opening %s', swarmci_file)
    with open(swarmci_file, 'r') as f:
        swarmci_config = yaml.load(f)

    jsonschema.validate(swarmci_config, SCHEMA)

    build_task = build_tasks_hierarchy(swarmci_config)

    logger.debug('starting build')
    build_task.execute()

    if build_task.successful:
        logger.info('all stages completed successfully!')
    else:
        logger.error('some stages did not complete successfully. :(')

    for line in get_task_results(build_task):
        print(line)

    if not build_task.successful:
        sys.exit(1)
