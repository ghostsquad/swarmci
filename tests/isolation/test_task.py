# coding=utf-8
import pytest
from assertpy import assert_that
from mock import Mock, call

from swarmci.task import Task, Build, Stage, Job
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner


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


def describe_build():
    def describe_init():
        def given_runner():
            def expect_runner_set():
                subject = Build('foo', runner='foo')
                assert_that(subject._runner).is_equal_to('foo')

        def given_no_runner():
            def expect_runner_is_serial_runner():
                subject = Build('foo')
                assert_that(subject._runner).is_instance_of(SerialRunner)


def describe_stage():
    def describe_init():
        def given_runner():
            def expect_runner_set():
                subject = Stage('foo', runner='foo')
                assert_that(subject._runner).is_equal_to('foo')

        def given_no_runner():
            def expect_runner_is_threaded_runner():
                subject = Stage('foo', thread_pool_executor='foo')
                assert_that(subject._runner).is_instance_of(ThreadedRunner)

            def given_no_thread_pool_executor():
                def expect_value_error():
                    with pytest.raises(ValueError) as exc_info:
                        Stage('foo')

                    assert_that(str(exc_info.value)).matches('thread_pool_executor is required')


def describe_job():
    def describe_init():
        def given_runner():
            def expect_runner_set():
                subject = Job('foo', runner='foo')
                assert_that(subject._runner).is_equal_to('foo')

        def given_no_runner():
            def expect_runner_is_docker_runner():
                subject = Job('foo', image='foo')
                assert_that(subject._runner).is_instance_of(DockerRunner)
