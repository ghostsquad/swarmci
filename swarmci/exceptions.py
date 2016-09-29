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


class DockerCommandFailedException(SwarmCIException):
    def __init__(self, *args, **kwargs):
        self._output = kwargs.pop('output')
        self._exit_code = kwargs.pop('exit_code')
        self._cmd = kwargs.pop('cmd')
        super(DockerCommandFailedException, self).__init__(*args, **kwargs)

    @property
    def output(self):
        return self._output

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def cmd(self):
        return self._cmd
