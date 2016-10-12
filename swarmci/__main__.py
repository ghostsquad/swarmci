import traceback
import sys
import logging
from swarmci import main

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception:
        logger.error("An Unhandled Exception Occurred", exc_info=True)
        traceback.print_exc()
        sys.exit(2)
