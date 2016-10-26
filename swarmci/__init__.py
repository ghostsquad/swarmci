import sys
import traceback
import argparse
import logging
import os
import yaml
import colorlog
from uuid import uuid4
from colored import fg, attr
from concurrent.futures import ThreadPoolExecutor
from swarmci.util import get_logger
from swarmci.errors import SwarmCIError
from swarmci.task import Build, Stage, Job, Command
from swarmci.version import __version__

logger = get_logger(__name__)


def build_command_tasks(job):
    return map(lambda x: Command(x), job['commands'])


def build_job_tasks(stage):
    def create_job_task(job):
        commands = build_command_tasks(job)
        return Job(job['name'], image=job['image'], sub_tasks=commands)

    return map(lambda j: create_job_task(j), stage['jobs'])


def build_stage_tasks(stages, thread_pool_executor):
    def create_build_task(stage):
        jobs = build_job_tasks(stage)
        return Stage(stage['name'], thread_pool_executor=thread_pool_executor, sub_tasks=jobs)

    return map(create_build_task, stages)


def validate_stages(stages):
    if stages is None:
        raise SwarmCIError('Did not find "stages" key in the .swarmci file.')
    elif not isinstance(stages, list):
        raise SwarmCIError('The value of the "stages" key should be a list in the .swarmci file.')


def build_tasks_hierarchy(swarmci_config):
    stages = swarmci_config.pop('stages', None)
    validate_stages(stages)

    stage_tasks = build_stage_tasks(stages, ThreadPoolExecutor(max_workers=25))

    return Build(str(uuid4()), sub_tasks=stage_tasks)


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


def print_failure_results(task):
    # everything is a task, but only COMMANDS have meaningful output
    print("")
    print("{}============== COMMAND FAILURES =============={}".format(fg(1), attr(0)))
    _print_failure_results(task.subtasks)
    print("{}=============================================={}".format(fg(1), attr(0)))


def _print_failure_results(tasks):
    for task in tasks:
        if type(task) is Command and not task.successful and task.runtime is not None:
            print("")
            print(task.name)
            print("{}----------------------------------------------{}\n".format(fg(1), attr(0)))
            if task.exc_info is not None:
                traceback.print_exception(*task.exc_info)
                print("")

            if task.results is not None and len(task.results) > 0:
                for line in task.results:
                    print(line)

        _print_failure_results(task.subtasks)


def print_task_results(task):
    print("")

    def get_status_string(color, symbol, count, status):
        return "{}{} {} {}{}".format(fg(color), symbol, count, status, attr(0))

    successful, failed, skipped = _print_task_results([task])

    success_msg = get_status_string(2, "\u2713", successful, "successful") if successful > 0 else ""

    if failed > 0:
        skipped_msg = get_status_string(3, "\u2933", skipped, "skipped") if skipped > 0 else ""
        failed_msg = get_status_string(1, "\u2717", failed, "failed") if failed > 0 else ""

        print("\n  {}\n".format(" ".join([failed_msg, skipped_msg, success_msg])))
    else:
        print("\n  {}\n".format(success_msg))


def _print_task_results(tasks, indent=2):
    success = 0
    failed = 0
    skipped = 0

    for task in tasks:
        if task.successful:
            success += 1
            symbol = "\u2713"
            desired_fg = fg(2)
        elif task.runtime is None:
            skipped += 1
            symbol = "\u2933"
            desired_fg = fg(3)
        else:
            failed += 1
            symbol = "\u2717"
            desired_fg = fg(1)

        left_pad = " " * indent
        line = "{}{}{}{} {} ({})".format(left_pad, desired_fg, symbol, attr(0), task.name, task.runtime_str)
        print(line)
        new_success, new_failed, new_skipped = _print_task_results(task.subtasks, indent=indent + 2)
        success += new_success
        failed += new_failed
        skipped += new_skipped

    return success, failed, skipped


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

    build_task = build_tasks_hierarchy(swarmci_config)

    logger.debug('starting build')
    build_task.execute()

    if build_task.successful:
        logger.info('all stages completed successfully!')
    else:
        logger.error('some stages did not complete successfully. :(')
        print_failure_results(build_task)

    print_task_results(build_task)

    if not build_task.successful:
        sys.exit(1)
