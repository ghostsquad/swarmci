#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging


def get_logger(name):  # pragma: no cover
    """creates a logger with NullHandler"""
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger


def raise_(ex):
    """
    this allows for some shorthand like
    x = y or raise_(ValueError)
    :param ex: Exception to raise
    """
    raise ex
