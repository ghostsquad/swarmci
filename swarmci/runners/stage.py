from swarmci.util import get_logger
from swarmci.runners import TaskRunner

logger = get_logger(__name__)

class StageRunner(TaskRunner):
    def __init__(self, job_runner, run_all_strategy):
        super(StageRunner, self).__init__(run_all_strategy, 'stage')
        self.job_runner = job_runner
        self.run_all_strategy = run_all_strategy

    def run(self, stage):
        with self.job_runner as j:
            return j.run_all(stage.jobs)
