# coding=utf-8


class Subscriber(object):
    """
    Receiver of events after registering with a publisher
    """
    def update(self, message):
        """
        This is the method that will be called when a Publisher dispatches
        an event to this subscriber
        :param message: object
        """
        raise NotImplementedError


class Publisher(object):
    """
    Publishes messages to subscribers
    """

    def __init__(self, events):
        if isinstance(events, str):
            events = [events]
        # maps event names to subscribers
        # str -> dict
        self.events = {event: dict()
                       for event in events}

    def get_subscribers(self, event):
        """
        Get a list of subscribers subscribed to a specific event
        :param event: str
        :return: list of objects
        """
        return self.events[event]

    def register(self, event, who, callback=None):
        """
        Register a subscriber to a specific event
        :param event: str
        :param who: Subscriber
        :param callback: func or None
            if None is provided, the `update` method will be called
            on the subscriber
        """
        if callback is None:
            callback = getattr(who, 'update')
        self.get_subscribers(event)[who] = callback

    def unregister(self, event, who):
        """
        Remove a subscriber from being updated on a specific event
        :param event: str
        :param who: Subscriber
        """
        del self.get_subscribers(event)[who]

    def dispatch(self, event, message):
        """
        Call subscriber callbacks who are subscribed to the given event
        providing the message payload to that func
        :param event: str
        :param message: object
        """
        for subscriber, callback in self.get_subscribers(event).items():
            callback(message)
