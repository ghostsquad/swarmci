import tarfile
from io import BytesIO
import os
from uuid import uuid4
from swarmci.util import get_logger
from swarmci.exceptions import DockerCommandFailedException

logger = get_logger(__name__)


class Container(object):
    """
    A class representing a running container
    """
    def __init__(self, image, host_config, docker, name=None, env=None, remove=True):
        self.image = image
        self.host_config = host_config
        self.docker = docker
        self.name = name or 'swarmci_' + str(uuid4())
        self.env = env
        self.remove = remove

        cmd = '/bin/sh -c "while true; do sleep 1000; done"'

        self.id = self.docker.create_container(image=image,
                                               host_config=host_config,
                                               name=name,
                                               environment=env or {},
                                               command=cmd)['Id']

        self.docker.start(self.id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """stop and optionally remove the container"""
        if self.remove:
            logger.debug('removing container!')
            self.docker.remove_container(container=self.id, v=True, force=True)
        else:
            logger.debug('stopping container!')
            self.docker.stop(container=self.id)

    def cp(self, src, dest):
        """
        copy a file or directory into the container
        :param src:
        :param dest:
        """
        src = os.path.abspath(src)
        arcname = os.path.basename(src.rstrip('/'))

        logger.debug('attempting to copy %s to %s', src, dest)

        with BytesIO() as c:
            with tarfile.open(mode='w', fileobj=c) as t:
                t.add(src, arcname=arcname)
            data = c.getvalue()

        self.docker.put_archive(self.id, path=dest, data=data)

    def execute(self, cmd, out_func=None):
        """
        Prepares a command to be executed within the container
        :param cmd: cmd to run
        :param out_func: a func to call for each line of output received
            this func should take a string argument
        :return: nothing. raises an exception if the command fails
        """

        if out_func is None:
            def out_func():
                pass

        exec_id = self.docker.exec_create(container=self.id, cmd=cmd, tty=True)['Id']
        logger.debug('starting exec [%s] in %s (%s)', cmd, self.name, self.id)
        output = []
        for line in self.docker.exec_start(exec_id=exec_id, stream=True):
            line = line.decode().rstrip()
            output.append(line)
            out_func(line)
            logger.info(line)

        logger.debug("attempting to get exit_code")
        exit_code = int(self.docker.exec_inspect(exec_id)['ExitCode'])
        logger.debug("got exitcode %s", exit_code)

        if exit_code != 0:
            msg = 'command [{}] returned exitcode [{}]'.format(cmd, exit_code)
            raise DockerCommandFailedException(message=msg, exit_code=exit_code, cmd=cmd, output=output)
