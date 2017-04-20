from assertpy import assert_that
from mock import mock, create_autospec
import pytest
from pytest_describe import behaves_like
from docker import Client as DockerClient
from concurrent.futures import ThreadPoolExecutor
from swarmci.docker import Container
from swarmci.task import Task
from swarmci.runners import SerialRunner, ThreadedRunner, DockerRunner
from swarmci.errors import TaskFailedError


def create_task_mock(count=1):
    m = []
    for i in range(0, count):
        m.append(create_autospec(Task, spec_set=True))

    if count == 1:
        return m[0]
    return m


def a_runner():
    def describe_run():
        def expect_task_execute_called(runner_fixture):
            mock_task = create_task_mock()
            runner_fixture.run(task=mock_task)
            mock_task.execute.assert_called_once()

    def describe_run_all():
        def given_single_task():
            def when_task_fails():
                def expect_raises_task_failed_error(runner_fixture):
                    task_mock = create_task_mock()
                    task_mock.successful = False

                    with pytest.raises(TaskFailedError) as exc_info:
                        runner_fixture.run_all([task_mock])

                    assert_that(str(exc_info.value)).matches(r'Failure')

            def when_task_succeeds():
                def expect_does_not_raise_task_failed_error(runner_fixture):
                    task_mock = create_task_mock()
                    task_mock.successful = True

                    runner_fixture.run_all([task_mock])

        def given_multiple_tasks():
            def when_any_task_fails():
                def expect_raises_task_failed_error(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = True
                    task2_mock.successful = False

                    with pytest.raises(TaskFailedError) as exc_info:
                        runner_fixture.run_all([task1_mock, task2_mock])

                    assert_that(str(exc_info.value)).matches(r'Failure')

            def when_all_tasks_succeed():
                def expect_not_to_raise_error(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = True
                    task2_mock.successful = True

                    runner_fixture.run_all([task1_mock, task2_mock])


def a_serial_runner():
    def describe_run_all_serial_behavior():
        def given_many_tasks():
            def when_first_task_fails():
                def expect_later_tasks_not_run_raise_task_failed_error(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = False

                    with pytest.raises(TaskFailedError) as exc_info:
                        runner_fixture.run_all([task1_mock, task2_mock])

                    assert_that(str(exc_info.value)).matches(r'Failure')

                    task1_mock.execute.assert_called_once()
                    task2_mock.execute.assert_not_called()


@behaves_like(a_runner, a_serial_runner)
def describe_serial_runner():
    @pytest.fixture(scope='module')
    def runner_fixture():
        return SerialRunner()


@behaves_like(a_runner)
def describe_threaded_runner():

    @pytest.fixture(scope='module')
    def runner_fixture():
        return ThreadedRunner(thread_pool_executor=ThreadPoolExecutor(max_workers=2))

    def describe_run_all_threaded_behavior():
        def given_many_tasks():
            def when_first_task_fails():
                def expect_later_tasks_still_run(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = False

                    with pytest.raises(TaskFailedError):
                        runner_fixture.run_all([task1_mock, task2_mock])

                    task1_mock.execute.assert_called_once()
                    task2_mock.execute.assert_called_once()


@behaves_like(a_runner, a_serial_runner)
def describe_docker_runner():

    @pytest.fixture()
    def cn_fixture():
        return create_autospec(Container, spec_set=True)

    @pytest.fixture()
    def task_fixture():
        return create_autospec(Task, spec_set=True)

    @pytest.fixture(scope='module')
    def runner_fixture():
        docker_mock = create_autospec(DockerClient, spec_set=True)
        return DockerRunner('foo_image', docker=docker_mock)

    def describe_run_in_docker():

        def expect_command_executed_in_container(cn_fixture):
            expected_command = 'test task'
            DockerRunner.run_in_docker(expected_command, cn=cn_fixture)
            cn_fixture.execute.assert_called_once_with(expected_command, out_func=None)

    def describe_run_all_container_behavior():

        def expect_cn_passed_to_task(cn_fixture, task_fixture):
            docker_mock = create_autospec(DockerClient, spec_set=True)
            expected_command = 'test cmd'
            task_fixture.name = expected_command

            subject = DockerRunner('foo_image', docker=docker_mock, cn=cn_fixture)

            subject.run_all([task_fixture])
            task_fixture.execute.assert_called_once_with(cn=mock.ANY)
