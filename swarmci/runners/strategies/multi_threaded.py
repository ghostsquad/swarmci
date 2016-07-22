import logging
import threading
from time import sleep
from queue import Queue, Empty
from swarmci.util import get_logger, synchronized

logger = get_logger(__name__)


def run_multithreaded(things, func, name=None, max_workers=None):
    if max_workers is None:
        max_workers = len(things)

    logger.info('running with %s workers', max_workers)

    queue = CompletionTrackingQueue()
    queue.total = len(things)

    for task in things:
        logger.debug('Queueing {name} ({id})'.format(name=task.name, id=task.id))
        queue.put(task)

    # Create worker threads
    for x in range(max_workers):
        worker = JobWorker(queue, func)
        worker.start()

    main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        logging.debug('exiting %s', t.getName())
        t.join()

    logger.debug("queue is now empty, checking results")
    for task in things:
        logger.debug('task %s result: %s', task.name, task.result)
        if not task.result:
            return False

    return True


class CompletionTrackingQueue(Queue):
    def __init__(self):
        super(CompletionTrackingQueue, self).__init__()
        self._completed = 0
        self.total = 0
        self._lock = threading.RLock()

    @property
    @synchronized('_lock')
    def completed(self):
        return self._completed

    @completed.setter
    @synchronized('_lock')
    def completed(self, value):
        self._completed = value


class JobWorker(threading.Thread):
    """
    Runs a single job, picking up jobs from a synchronized queue
    """

    def __init__(self, queue, run_job_func):
        threading.Thread.__init__(self)
        self.queue = queue
        self._run_job = run_job_func
        self.logger = get_logger(__name__)

    def run(self):
        """
        runs the provided job function on the job object
        """
        while self.queue.completed < self.queue.total:
            try:
                job = self.queue.get(block=False, timeout=0.2)
                self.logger.debug('received %s from queue', job.name)
                result = self._run_job(job)
                self.logger.debug('received result %s from job %s', result, job.name)
                job.result = result
                self.queue.completed += 1
            except Empty:
                sleep(0.2)
            except Exception:
                self.logger.exception("Unhandled Exception Occurred", exc_info=True)
                job.result = False
                self.queue.completed += 1
