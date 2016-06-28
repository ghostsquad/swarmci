import time
import copy
from uuid import uuid4
from six import iteritems
from .exceptions import (RunnableException, IdentifiableException, BuildAgentException)


class Runnable(object):
    def __init__(self, **kwargs):
        self.start = None
        self.end = None
        self.runtime = None

    def start(self):
        if self.start is not None:
            raise RunnableException('task already started.')
        self.start = time.time()

    def stop(self):
        if self.start is None:
            raise RunnableException('task cannot be stopped without being started first.')

        if self.end is not None:
            raise RunnableException('task has already been stopped.')

        self.end = time.time()
        self.runtime = self.start - self.end

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class Identifiable(object):
    def __init__(self, **kwargs):
        self.id = str(uuid4())
        self.name = kwargs.pop('name', None)
        if self.name is None:
            raise IdentifiableException('an identifiable object must have a name!')


class Job(Runnable, Identifiable):
    def __init__(self,
                 images,
                 tasks,
                 clone=True,
                 env=None,
                 build=None,
                 after_failure=None,
                 finally_task=None,
                 **kwargs):
        super(Job, self).__init__(**kwargs)

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

        if len(self.images) == 1 and (
            self.env is None or (
                    type(self.env) is list and len(self.env) == 1
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


class Task(Runnable, Identifiable):
    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)


class Stage(Runnable, Identifiable):
    def __init__(self, jobs, **kwargs):
        super(Stage, self).__init__(**kwargs)

        if jobs is None or type(jobs) is not dict:
            raise BuildAgentException('jobs within a stage must be a dictionary!')

        self.jobs = []
        for name, _job in iteritems(jobs):

            f = _job.pop('finally', None)
            if f is not None:
                _job['finally_task'] = f

            self.jobs.append(Job(
                images=_job.pop('images', _job.pop('image', None)),
                tasks=_job.pop('tasks', _job.pop('task', None)),
                name=name,
                **_job
            ))
