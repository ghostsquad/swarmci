from threading import Thread


class JobWorker(Thread):
    """
    Runs a single job, picking up jobs from a synchronized queue
    """

    def __init__(self, queue, run_job_func):
        Thread.__init__(self)
        self.queue = queue
        self._run_job = run_job_func

    def run(self):
        """
        runs the provided job function on the job object
        """
        while True:
            job = self.queue.get()
            self._run_job(job)
            self.queue.task_done()
