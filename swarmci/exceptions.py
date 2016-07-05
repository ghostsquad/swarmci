# -*- coding: utf-8 -*-
"""
This module is a central location for all SwarmCI exceptions
"""


class SwarmCIException(Exception):
    """
    Base exception class; all SwarmCI-specific exceptions should subclass this
    """
    strerror = None

    def __init__(self, message=''):
        super(SwarmCIException, self).__init__(message)
        self.strerror = message


class TaskException(SwarmCIException):
    def __init__(self, *args, **kwargs):
        super(TaskException, self).__init__(*args, **kwargs)


class InvalidOperationException(SwarmCIException):
    def __init__(self, *args, **kwargs):
        super(InvalidOperationException, self).__init__(*args, **kwargs)


class BuildAgentException(SwarmCIException):
    def __init__(self, *args, **kwargs):
        super(BuildAgentException, self).__init__(*args, **kwargs)
