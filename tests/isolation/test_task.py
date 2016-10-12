from mock import Mock, call
from assertpy import assert_that
import pytest
from swarmci.task import Task


def describe_task():
    def describe_init():
        def given_valid_name():
            def sets_name_property():
                subject = Task('test')
                assert_that(subject.name).is_equal_to('test')

        def given_invalid_name():
            def raises_error():
                with pytest.raises(ValueError) as excinfo:
                    Task(None)
                assert_that(str(excinfo.value)).is_equal_to('tasks must have a name')

    def describe_execute():
        def given_subclass_overriding_execute_private_method():
            def records_timing_of_the_task_execution():
                parent_mock = Mock()
                parent_mock.time = Mock()
                parent_mock.time.side_effect = [1, 5]
                parent_mock.exec_func = Mock()

                class TestTask(Task):
                    def _execute(self, *args, **kwargs):
                        parent_mock.exec_func()

                subject = TestTask('foo', parent_mock.exec_func, tm=parent_mock.time)
                subject.execute()

                parent_mock.assert_has_calls([call.time(), call.exec_func(), call.time()])
                assert_that(subject.runtime).is_equal_to(4)

            def expect_args_kwargs_passed_to_exec_func():
                class TestTask(Task):
                    pass

                subject = TestTask('foo')
                TestTask._execute = Mock()
                exp_args = ['hello', 'world']
                exp_kwargs = {'foo': 'bar'}
                subject.execute(*exp_args, **exp_kwargs)
                TestTask._execute.assert_called_once_with(*exp_args, **exp_kwargs)
