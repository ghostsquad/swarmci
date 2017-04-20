# coding=utf-8
import pytest
from assertpy import assert_that
from mock import Mock

from swarmci.simple_pub_sub import Publisher


def describe_publisher():
    def describe_init():
        def given_list_as_events_param():
            def expect_list_contents_mapped_to_events_dict():
                pub = Publisher(['foo', 'bar'])
                assert_that(pub.events).contains_key('foo')
                assert_that(pub.events).contains_key('bar')

        def given_string_as_events_param():
            def expect_events_set_to_dict_with_single_entry():
                pub = Publisher('foo')
                assert_that(pub.events).is_length(1)
                assert_that(pub.events).contains_key('foo')

    def describe_get_subscribers():
        def given_no_registered_subscribers():
            def expect_return_empty_dict():
                result = Publisher('foo').get_subscribers('foo')
                assert_that(result).is_instance_of(dict)
                assert_that(result).is_empty()

        def given_subscriber_for_different_event():
            def expect_return_empty_dict():
                pub = Publisher(['foo', 'bar'])
                pub.register('foo', 'bob', lambda: None)
                result = pub.get_subscribers('bar')
                assert_that(result).is_instance_of(dict)
                assert_that(result).is_empty()

        def given_non_existent_event():
            def expect_undefined_event_error_raised():
                with pytest.raises(KeyError) as exc_info:
                    Publisher('foo').get_subscribers('bar')

                assert_that(str(exc_info.value)).matches('bar')

    def describe_register():
        def when_callback_is_none():
            def when_message_dispatched():
                def expect_update_method_called_on_who():
                    event = 'foo'
                    pub = Publisher(event)
                    subscriber_mock = Mock()
                    pub.register(event, subscriber_mock)
                    expected_msg = 'my message'

                    pub.dispatch(event, expected_msg)

                    subscriber_mock.update.assert_called_once_with(expected_msg)

        def when_callback_provided():
            def when_message_dispatched():
                def expect_callback_is_called():
                    event = 'foo'
                    pub = Publisher(event)
                    subscriber_mock = Mock()
                    callback_mock = Mock()

                    pub.register(event, subscriber_mock, callback_mock)
                    expected_msg = 'my message'

                    pub.dispatch(event, expected_msg)

                    callback_mock.assert_called_once_with(expected_msg)
                    subscriber_mock.update.assert_not_called()

    def describe_unregister():
        def given_registered_subscriber():
            def when_dispatch_called():
                def expect_unregistered_subscriber_not_updated():
                    event = 'foo'
                    pub = Publisher(event)
                    subscriber_mock = Mock()

                    pub.register(event, subscriber_mock)
                    pub.unregister(event, subscriber_mock)

                    pub.dispatch(event, 'my message')

                    subscriber_mock.update.assert_not_called()
