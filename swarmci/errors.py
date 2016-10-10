# -*- coding: utf-8 -*-
"""
This module is a central location for all SwarmCI exceptions
"""


class SwarmCIError(Exception):
    """
    Base exception class; all SwarmCI-specific exceptions should subclass this
    """
    strerror = None

    def __init__(self, message=''):
        super(SwarmCIError, self).__init__(message)
        self.strerror = message


class TaskFailedError(SwarmCIError):
    def __init__(self, *args, **kwargs):
        super(TaskFailedError, self).__init__(*args, **kwargs)


class InvalidOperationError(SwarmCIError):
    def __init__(self, *args, **kwargs):
        super(InvalidOperationError, self).__init__(*args, **kwargs)


class DockerCommandFailedError(SwarmCIError):
    def __init__(self, *args, **kwargs):
        self._output = kwargs.pop('output')
        self._exit_code = kwargs.pop('exit_code')
        self._cmd = kwargs.pop('cmd')
        super(DockerCommandFailedError, self).__init__(*args, **kwargs)

    @property
    def output(self):
        return self._output

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def cmd(self):
        return self._cmd
