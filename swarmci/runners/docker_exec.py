import tarfile
from io import BytesIO
import os
from uuid import uuid4
from docker import Client as DockerClient
from swarmci.util import get_logger

logger = get_logger(__name__)


class DockerExecRunner(object):
    def __init__(self, docker_runner):
        self.docker_runner = docker_runner

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run_all(self, tasks, env=None):
        with self.docker_runner.start_container(env) as cn:
            for task in tasks:
                logger.info('starting task [%s] in %s', task.name, cn.id[0:11])
                result = self.run(task, cn)
                if not result:
                    logger.error('failure detected, skipping further tasks')
                    return False

            return True

    def run(self, task, cn):
        dexec = cn.execute(task.name)
        logger.info("----BEGIN STDOUT----")
        for line in dexec.start():
            logger.info(line)

        logger.info("----END STDOUT----")

        logger.debug("received exit code %s", dexec.exit_code)
        if dexec.exit_code != 0:
            logger.error("task failed!")
            return False

        return True


class DockerRunner(object):
    """
    How to naturally run tasks within docker containers
    """
    def __init__(self, image, name=None, remove=True, url=':4000', **kwargs):
        self.docker = DockerClient(base_url=url, version='1.24')
        self.image = image

        self.name = name

        self.remove = remove

        kwargs.setdefault('binds', [])
        kwargs.setdefault('network_mode', 'bridge')

        self.host_config = self.docker.create_host_config(**kwargs)
        self.id = None

    def start_container(self, env):
        """create a running container (just sleeps)"""
        cn = container(self.image, self.host_config, self.name, self.docker, env=env)
        return cn


class container(object):
    """
    A class representing a running container
    """
    def __init__(self, image, host_config, name, docker, env, remove=True):
        self.docker = docker

        self.name = name or 'swarmci_' + str(uuid4())

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
        if self.remove:
            logger.debug('removing container!')
            self.docker.remove_container(container=self.id, v=True, force=True)
        else:
            logger.debug('stopping container!')
            self.docker.stop(container=self.id)

    def close(self):
        """stop and optionally remove the container"""
        self.__exit__(None, None, None)

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

    def execute(self, cmd):
        """
        Prepares a command to be executed within the container
        :param cmd: cmd to run
        :return: DockerCommandExecution object
        """
        return DockerCommandExecution(cmd, self)


class DockerCommandExecution(object):
    """
    To begin execution, call start() which is a generator and yields stdout/err.
    The exit code is populated after the stream completes.
    """
    def __init__(self, cmd, cn):
        self.cmd = cmd
        self.cn = cn
        self.docker = cn.docker
        self.exec_id = self.docker.exec_create(container=cn.id, cmd=cmd, tty=True)['Id']
        self.exit_code = None

    def start(self):
        """stream the stdout from a exec command"""
        logger.debug('starting exec [%s] in %s (%s)', self.cmd, self.cn.name, self.cn.id)
        for line in self.docker.exec_start(exec_id=self.exec_id, stream=True):
            line = line.decode().rstrip()
            yield line

        logger.debug("attempting to get exit_code")
        self.exit_code = int(self.docker.exec_inspect(self.exec_id)['ExitCode'])
        logger.debug("got exitcode %s", self.exit_code)
