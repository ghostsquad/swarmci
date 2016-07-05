import logging
import tarfile
from docker import Client as DockerClient
from uuid import uuid4
from os import path
from io import BytesIO


def get_logger(name):
    _logger = logging.getLogger(name)
    _logger.addHandler(logging.NullHandler())
    return _logger

logger = get_logger(__name__)


class container(object):
    def __init__(self,
                 image='docker.service.audsci.net/salt/minion:centos7',
                 name=None,
                 mounts=None,
                 remove=True,
                 docker_client=None,
                 docker_sock='unix://var/run/docker.sock',
                 host_config_kwargs=None,
                 **kwargs):

        self.image = image
        if not name:
            self.name = 'formula_test_' + str(uuid4())

        if mounts is None:
            mounts = []

        self.remove = remove

        if not docker_client:
            self.docker = DockerClient(base_url=docker_sock, **kwargs)

        if not host_config_kwargs:
            host_config_kwargs = {
                'network_mode': 'bridge'
            }

        host_config = self.docker.create_host_config(binds=mounts,
                                                     **host_config_kwargs)

        self.id = self.docker.create_container(image=self.image,
                                               host_config=host_config,
                                               name=name,
                                               command='while true; do foo; sleep 2; done')['Id']

        self.docker.start(self.id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.remove:
            logger.debug('removing container!')
            self.docker.remove_container(container=self.id, v=True, force=True)
        else:
            logger.debug('stopping container!')
            self.docker.stop(container=self.id)

    def close(self):
        self.__exit__(None, None, None)

    def cp(self, src, dest):
        src = path.abspath(src)
        arcname = path.basename(src.rstrip('/'))

        with BytesIO() as c:
            with tarfile.open(mode='w', fileobj=c) as t:
                t.add(src, arcname=arcname)
            data = c.getvalue()

        self.docker.put_archive(self.id, path=dest, data=data)

    def execute(self, cmd):
        """
        Prepares a command to be executed within the container
        :param cmd: cmd to run
        :return: Execution object
        """

        exec_id = self.docker.exec_create(container=self.id, cmd=cmd)['Id']

        d_exec = Execution(cmd)

        def get_output_stream():
            for line in self.docker.exec_start(exec_id=exec_id, stream=True):
                line = line.decode().rstrip()
                yield line

            exec_inspect = self.docker.exec_inspect(exec_id)
            d_exec.exit_code = exec_inspect['ExitCode']

        d_exec.set_stream(get_output_stream)

        return d_exec


class Execution(object):
    """
    To begin execution, call stream() which is a generator.
    The exit code is populated after the stream completes.
    """
    def __init__(self, cmd):
        self.cmd = cmd
        self.exit_code = None
        self._stream = None

    def stream(self):
        yield self._stream()

    def set_stream(self, stream_func):
        self._stream = stream_func
