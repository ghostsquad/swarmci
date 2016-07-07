from swarmci.task import Task
from swarmci.util import get_logger


class Stage(Task):
    """SwarmCI uses Stages, which consist of Jobs, which consist of Tasks"""
    def __init__(self, name, jobs):
        super(Stage, self).__init__(name)

        self.logger = get_logger(__name__)

        if jobs is None or type(jobs) is not list:
            raise ValueError('jobs must be a list!')

        self.jobs = jobs