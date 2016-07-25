from swarmci.util import get_logger
from swarmci.runners import TaskRunner

logger = get_logger(__name__)


class JobRunner(TaskRunner):
    """Runs tasks within a docker container"""
    def __init__(self, task_runner, run_all_strategy):
        super(JobRunner, self).__init__(run_all_strategy, 'job')
        self.task_runner = task_runner
        self.run_all_strategy = run_all_strategy

    def run(self, job):
        """Runs all tasks within the same container for a given job"""
        logger.info("starting job %s", job.name)
        with self.task_runner as t:
            return t.run_all(job.tasks, env=job.env)
