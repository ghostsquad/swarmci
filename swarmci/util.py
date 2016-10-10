#!/usr/bin/python
# -*- coding: UTF-8 -*-
import logging
from colored import fg, attr

def get_logger(name):
    """creates a logger with NullHandler"""
    _logger = logging.getLogger(name)
    _logger.addHandler(logging.NullHandler())
    return _logger


# this allows for some shorthand like
# x = y or raise_(ValueError)
def raise_(ex):
    raise ex


def print_task_results(task):
    print("\n")

    total, failed = _print_task_results([task])

    if failed > 0:
        symbol = "\u2717"
        desired_fg = fg(1)
    else:
        symbol = "\u2713"
        desired_fg = fg(2)

    print("\n  {}{} {} tasks successful, {} tasks failed{}\n".format(desired_fg, symbol, total-failed, failed, attr(0)))


def _print_task_results(tasks, indent=2):
    total = len(tasks)
    failed = 0

    for task in tasks:
        if task.successful:
            symbol = "\u2713"
            desired_fg = fg(2)
        else:
            symbol = "\u2717"
            failed += 1
            desired_fg = fg(1)

        left_pad = " " * indent
        line = "{}{}{}{} {} ({})".format(left_pad, desired_fg, symbol, attr(0), task.name, task.runtime_str)
        print(line)
        new_total, new_failed = _print_task_results(task.subtasks, indent=indent + 2)
        total += new_total
        failed += new_failed

    return total, failed
