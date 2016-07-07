import copy
from swarmci.util import get_logger
from swarmci.task import Task


class Job(Task):
    """
    Encapsulates all information needed to run a series of commands within a container
    """
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

        self.tasks = []

        for task in tasks:
            self.tasks.append(Task(task))

        self.clone = clone
        self.env = env
        self.build = build
        self.after_failure = after_failure
        self.finally_task = finally_task

    def split(self):
        """
        Splits job into multiple jobs if it contains multiple images or env var sets
        :return: list of Jobs
        """
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
