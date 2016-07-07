from swarmci.util import get_logger

logger = get_logger(__name__)


class TaskRunner(object):
    def __init__(self, run_all_strategy, name):
        self.name = name
        self.run_all_strategy = run_all_strategy

    def run(self, task):
        raise NotImplementedError

    def run_all(self, tasks):
        return self.run_all_strategy(tasks, self.run, self.name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def close(self):
        pass
