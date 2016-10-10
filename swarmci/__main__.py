import traceback
import sys
import logging
from swarmci import main

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception as e:
        logger.exception("An Unhandled Exception Occurred", exc_info=e)
        traceback.print_exc()
        sys.exit(2)
