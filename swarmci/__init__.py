import time
import copy
from uuid import uuid4
from swarmci.util import get_logger
from .exceptions import InvalidOperationException


class Task(object):
    def __init__(self, name):
        self.logger = get_logger(__name__)
        self.id = str(uuid4())
        self.name = name
        if self.name is None:
            raise ValueError('an identifiable object must have a name!')

        self.start = None
        self.end = None
        self.runtime = None
        self.success = None
        self.result = None

    def start(self):
        if self.start is not None:
            raise InvalidOperationException('task already started.')
        self.start = time.time()

    def stop(self):
        if self.start is None:
            raise InvalidOperationException('task cannot be stopped without being started first.')

        if self.end is not None:
            raise InvalidOperationException('task has already been stopped.')

        self.end = time.time()
        self.runtime = self.start - self.end

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class Job(Task):
    def __init__(self,
                 name,
                 images,
                 tasks,
                 clone=True,
                 env=None,
                 build=None,
                 after_failure=None,
                 finally_task=None):

        super(Job, self).__init__(name)

        self.logger = get_logger(__name__)

        if type(images) is not list:
            images = [images]

        self.images = images

        if type(tasks) is not list:
            tasks = [tasks]

        self._tasks = tasks
        self.tasks = tasks
        self.clone = clone
        self.env = env
        self.build = build
        self.after_failure = after_failure
        self.finally_task = finally_task

    def split(self):
        new_jobs = []

        env_type = type(self.env)
        if len(self.images) == 1 and (
                            self.env is None or env_type is dict or (
                                env_type is list and len(self.env) == 1
                )
        ):
            return [self]

        base_clone = copy.deepcopy(self)
        delattr(base_clone, 'images')
        delattr(base_clone, 'env')

        if self.env is None:
            env_list = [None]
        elif type(self.env) is list:
            env_list = self.env
        else:
            env_list = [self.env]

        for image in self.images:
            new_image_list = [image]

            for env_set in env_list:
                clone = copy.deepcopy(base_clone)
                clone.images = new_image_list
                clone.env = env_set
                new_jobs.append(clone)

        return new_jobs


class Stage(Task):
    def __init__(self, name, jobs):
        super(Stage, self).__init__(name)

        self.logger = get_logger(__name__)

        if jobs is None or type(jobs) is not list:
            raise ValueError('jobs must be a list!')

        self.jobs = jobs
