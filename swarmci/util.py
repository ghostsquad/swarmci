#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging


def get_logger(name):
    """creates a logger with NullHandler"""
    _logger = logging.getLogger(name)
    _logger.addHandler(logging.NullHandler())
    return _logger


# this allows for some shorthand like
# x = y or raise_(ValueError)
def raise_(ex):
    raise ex
