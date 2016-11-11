# coding=utf-8
import pytest
from assertpy import assert_that
from mock import Mock, call, ANY

from swarmci.errors import TaskFailedError
from swarmci.task import Task, Build, Stage, Job, Command, RunnerTask
from swarmci.task import build_tasks_hierarchy, build_command_tasks
from swarmci.task import get_command_results
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner


# test task behaviors

def describe_task():
    def describe_init():
        def given_valid_name():
            def expect_sets_name_property():
                subject = Task('test')
                assert_that(subject.name).is_equal_to('test')

        def given_invalid_name():
            def expect_raises_error():
                with pytest.raises(ValueError) as exc_info:
                    Task(None)
                assert_that(str(exc_info.value)).is_equal_to('tasks must have a name')

        def given_sub_tasks_list():
            def expect_set_to_subtasks_property():
                expected_sub_tasks = []
                subject = Task('foo', sub_tasks=expected_sub_tasks)

                assert_that(subject.subtasks).is_equal_to(expected_sub_tasks)

    def describe_execute():
        def given_subclass_overriding_execute_private_method():
            def expect_records_timing_of_the_task_execution():
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

            def when_no_error_thrown():
                def expect_success_set():
                    class TestTask(Task):
                        def _execute(self, *args, **kwargs):
                            pass

                    subject = TestTask('foo')
                    assert_that(subject.successful).is_false()

                    subject.execute()

                    assert_that(subject.successful).is_true()

        def when_task_fails():
            def expect_exc_info_recorded():
                class TestTask(Task):
                    def _execute(self, *args, **kwargs):
                        raise TaskFailedError

                subject = TestTask('foo')
                subject.execute()

                assert_that(subject.exc_info).is_not_none()
                assert_that(subject.exc_info).is_length(3)

    def describe_runtime_str():
        def given_none_runtime():
            def expect_na_returned():
                subject = Task('foo')
                assert_that(subject.runtime_str).is_equal_to('N/A')

        def given_seconds_runtime():
            @pytest.mark.parametrize(['runtime', 'expected'], argvalues=[
                [20,      '0 min 20.00 sec'],
                [20.23,   '0 min 20.23 sec'],
                [20.2345, '0 min 20.23 sec'],
                [61,      '1 min 1.00 sec']
            ])
            def expect_formatted_output(runtime, expected):
                subject = Task('foo')
                subject._runtime = runtime

                assert_that(subject.runtime_str).is_equal_to(expected)


def describe_runner_task():
    def describe_execute():
        def expect_runner_run_all_called_with_subtasks():
            runner_mock = Mock()
            expected_subtasks = []

            subject = RunnerTask('foo', runner=runner_mock, sub_tasks=expected_subtasks)
            subject.execute()

            runner_mock.run_all.assert_called_once_with(expected_subtasks)


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

            def given_no_image():
                def expect_value_error_raised():
                    with pytest.raises(ValueError) as exc_info:
                        subject = Job('foo')

                    assert_that(str(exc_info.value)).is_equal_to('image is required if runner is not provided')


def describe_command():
    def describe_init():
        def describe_docker_run_parameter():
            def when_not_given():
                def expect_docker_run_private_property_set_to_run_in_docker_method():
                    subject = Command('foo')
                    assert_that(subject._docker_run).is_equal_to(DockerRunner.run_in_docker)

            def when_given():
                def expect_docker_run_private_property_set_to_value():
                    expected_value = 'some value'
                    subject = Command('foo', docker_run=expected_value)

                    assert_that(subject._docker_run).is_equal_to(expected_value)

    def describe_execute():
        def when_called():
            def expect_docker_run_property_called():
                docker_run_mock = Mock()
                expected_task_name = 'foo'
                subject = Command(expected_task_name, docker_run=docker_run_mock)

                subject.execute()

                docker_run_mock.assert_called_once_with(expected_task_name, out_func=ANY)

            def expect_results_stored():
                docker_run_mock = Mock()
                out_func_mock = Mock()


# test task factory methods


def describe_build_command_tasks():
    def maps_commands_key_to_build_command_tasks():
        first_command = 'first command'
        second_command = 'second_command'

        job = {
            'commands': [
                first_command,
                second_command
            ]
        }

        result = list(build_command_tasks(job))
        assert_that(result).is_length(2)
        assert_that(all([isinstance(x, Command) for x in result])).is_true()
        assert_that(result[0].name).is_equal_to(first_command)
        assert_that(result[1].name).is_equal_to(second_command)


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