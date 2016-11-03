# coding=utf-8
import pytest
from assertpy import assert_that
from mock import Mock, call

from swarmci.task import Task, Build, Stage, Job
from swarmci.task import build_tasks_hierarchy
from swarmci.task import get_command_results
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner


# test task behaviors

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

# test task factory methods


def describe_build_tasks_hierarchy():
    def expect_build_task_returned():
        config = {
            'stages': [
                {
                    'name': 'foo_stage',
                    'jobs': [
                        {
                            'name': 'foo_job',
                            'commands': [
                                'test command'
                            ]
                        }
                    ]
                }
            ]
        }
        task = build_tasks_hierarchy(config)

        assert_that(task).is_instance_of(Build)

# task results


def describe_get_command_results():

    no_output_found = '*** no output found! ***'

    def given_no_results():
        def given_no_exc_info():
            def expect_to_yield_no_output_found():
                results = list(get_command_results(Task(name='foo')))
                assert_that(results).is_length(3)
                assert_that(results)\
                    .contains_sequence('\x1b[38;5;1mfoo\x1b[0m',
                                       '\x1b[38;5;1m----------------------------------------------\x1b[0m\n',
                                       no_output_found)

    def given_results():
        def expect_to_yield_results():
            t = Task(name='foo')
            expected_results = ['this', 'is', 'results']
            t.results = expected_results
            actual_results = list(get_command_results(t))
            assert_that(actual_results).contains_sequence(*expected_results)
            assert_that(actual_results).does_not_contain(no_output_found)


def describe_decide_task_result_action():
    pass