from mock import Mock, call
from assertpy import assert_that
import pytest
from swarmci.task import Task, TaskType, TaskFactory


def dummy_func(): pass


def describe_task():
    def describe_init():
        def given_valid_task_type():
            def sets_task_type_property():
                subject = Task('test', TaskType.JOB, dummy_func)
                assert_that(subject.task_type).is_equal_to(TaskType.JOB)

        def given_invalid_task_type():
            def raises_error():
                with pytest.raises(ValueError) as excinfo:
                    Task('foo', 'mytype', dummy_func)
                assert_that(str(excinfo.value)).is_equal_to('task_type must be of type TaskType')

        def given_valid_name():
            def sets_name_property():
                subject = Task('test', TaskType.JOB, dummy_func)
                assert_that(subject.name).is_equal_to('test')

        def given_invalid_name():
            def raises_error():
                with pytest.raises(ValueError) as excinfo:
                    Task(None, 'mytype', dummy_func)
                assert_that(str(excinfo.value)).is_equal_to('tasks must have a name')

        def given_invalid_func():
            def raises_error():
                with pytest.raises(ValueError) as excinfo:
                    Task('foo', TaskType.JOB, 'foo')
                assert_that(str(excinfo.value)).is_equal_to('exec_func must be a callable')

    def describe_execute():
        def given_callable_exec_func():
            def records_timing_of_the_task_execution():
                parent_mock = Mock()
                parent_mock.time = Mock()
                parent_mock.time.side_effect = [1, 5]
                parent_mock.exec_func = Mock()

                subject = Task('foo', TaskType.JOB, parent_mock.exec_func, tm=parent_mock.time)
                subject.execute()

                parent_mock.assert_has_calls([call.time(), call.exec_func(), call.time()])
                assert_that(subject.runtime).is_equal_to(4)

            def expect_args_kwargs_passed_to_exec_func():
                exec_func_mock = Mock()
                subject = Task('foo', TaskType.JOB, exec_func_mock)
                exp_args = ['hello', 'world']
                exp_kwargs = {'foo': 'bar'}
                subject.execute(*exp_args, **exp_kwargs)
                exec_func_mock.assert_called_once_with(*exp_args, **exp_kwargs)


def describe_task_factory():
    def describe_create():
        @pytest.mark.parametrize(['task_type', 'kwargs'], [
            [TaskType.BUILD, {'stages': []}],
            [TaskType.STAGE, {'stage': {'name': 'test'}, 'jobs': [], 'thread_pool_executor': object}],
            [TaskType.JOB, {'job': {'name': 'test'}, 'commands': []}],
            [TaskType.COMMAND, {'cmd': 'my cmd'}]
        ])
        def expect_task_of_type_created(task_type, kwargs):
            task = TaskFactory().create(task_type, **kwargs)
            assert_that(task.task_type).is_equal_to(task_type)
            assert_that(callable(task.exec_func)).is_true()
