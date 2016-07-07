from swarmci.util import get_logger

logger = get_logger(__name__)


def stop_on_failure(items, func, item_type):
    """run function with item as args, stopping if func returns False"""
    for item in items:
        logger.info('starting %s [%s]', item_type, item.name)
        result = func(item)
        logger.debug('received result from %s %s of %s', item_type, item.name, result)
        if not result:
            logger.error('failure detected, skipping further %ss', item_type)
            return False

    return True
