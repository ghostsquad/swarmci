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


def get_swarmci_file(file, action):
    if file is not None:
        return file

    return action()


def get_default_swarmci_file():
    return os.path.join(os.getcwd(), '.swarmci')


def decide_build_success(task, success, fail):
    if task.successful:
        return success

    return fail


def setup_logging(debug):  # pragma: no cover
    logging_level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(logging_level)
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


def load_swarmci_config(file):
    swarmci_file = os.path.abspath(get_swarmci_file(file, get_default_swarmci_file))

    logger.debug('opening %s', swarmci_file)
    with open(swarmci_file) as f:
        swarmci_config = yaml.load(f)

    jsonschema.validate(swarmci_config, SCHEMA)
    return swarmci_config


def main(args):
    """
    This is the entry point for SwarmCI
    :param args: args from argparse
    """
    args = parse_args(args)

    setup_logging(args.debug)

    swarmci_config = load_swarmci_config(args.file)

    build_task = build_tasks_hierarchy(swarmci_config)

    logger.debug('starting build')
    build_task.execute()

    for line in get_task_results(build_task):
        print(line)

    end_action = decide_build_success(build_task, success=lambda: sys.exit(0), fail=lambda: sys.exit(1))
    end_action()
