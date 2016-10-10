import traceback
import sys
import logging
from swarmci import main
from swarmci.errors import TaskFailedError

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(asctime)s (%(threadName)-10s) [%(levelname)8s] - %(message)s")
        main(sys.argv[1:])
    except TaskFailedError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("An Unhandled Exception Occurred", exc_info=e)
        traceback.print_exc()
        sys.exit(2)
