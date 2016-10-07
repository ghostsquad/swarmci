from assertpy import assert_that
from mock import Mock, mock, create_autospec
import pytest
from pytest_describe import behaves_like
from docker import Client as DockerClient
from swarmci.docker import Container
from swarmci.task import Task
from swarmci.runners import RunnerBase, SerialRunner, ThreadedRunner, DockerRunner
from concurrent.futures import ThreadPoolExecutor


def create_task_mock(count=1):
    m = []
    for i in range(0, count):
        m.append(create_autospec(Task, spec_set=True))

    if count == 1:
        return m[0]
    return m


def a_runner():
    def describe_run():
        def given_task_not_successful():
            def expect_returns_false(runner_fixture):
                mock_task = create_task_mock()
                mock_task.successful = False

                assert_that(runner_fixture.run(task=mock_task)).is_false()

        def given_task_successful():
            def expect_returns_true(runner_fixture):
                mock_task = create_task_mock()
                mock_task.successful = True

                assert_that(runner_fixture.run(task=mock_task)).is_true()


def a_serial_runner():
    def describe_run_all():
        def given_single_task():
            def when_task_fails():
                def expect_return_false(runner_fixture):
                    task_mock = create_task_mock()
                    task_mock.successful = False

                    assert_that(runner_fixture.run_all([task_mock])).is_false()

            def when_task_succeeds():
                def expect_return_true(runner_fixture):
                    task_mock = create_task_mock()
                    task_mock.successful = True

                    assert_that(runner_fixture.run_all([task_mock])).is_true()

        def given_many_tasks():
            def when_first_task_fails():
                def expect_later_tasks_not_run_returns_false(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = False

                    assert_that(runner_fixture.run_all([task1_mock, task2_mock])).is_false()
                    task1_mock.execute.assert_called_once()
                    task2_mock.execute.assert_not_called()

            def when_any_task_fails():
                def expect_return_false(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = True
                    task2_mock.successful = False

                    assert_that(runner_fixture.run_all([task1_mock, task2_mock])).is_false()

            def when_all_tasks_succeed():
                def expect_return_true(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = True
                    task2_mock.successful = True

                    assert_that(runner_fixture.run_all([task1_mock, task2_mock])).is_true()


@behaves_like(a_runner)
def describe_runner_base():
    @pytest.fixture(scope='function')
    def runner_fixture():
        return RunnerBase()


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

    def describe_run_all_():
        def given_single_task():
            def when_task_fails():
                def expect_return_false(runner_fixture):
                    task_mock = create_task_mock()
                    task_mock.successful = False

                    assert_that(runner_fixture.run_all([task_mock])).is_false()

            def when_task_succeeds():
                def expect_return_true(runner_fixture):
                    task_mock = create_task_mock()
                    task_mock.successful = True

                    assert_that(runner_fixture.run_all([task_mock])).is_true()

        def given_many_tasks():
            def when_first_task_fails():
                def expect_later_tasks_still_run_returns_false(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = False

                    assert_that(runner_fixture.run_all([task1_mock, task2_mock])).is_false()
                    task1_mock.execute.assert_called_once()
                    task2_mock.execute.assert_called_once()

            def when_any_task_fails():
                def expect_return_false(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = True
                    task2_mock.successful = False

                    assert_that(runner_fixture.run_all([task1_mock, task2_mock])).is_false()

            def when_all_tasks_succeed():
                def expect_return_true(runner_fixture):
                    task1_mock, task2_mock = create_task_mock(count=2)
                    task1_mock.successful = True
                    task2_mock.successful = True

                    assert_that(runner_fixture.run_all([task1_mock, task2_mock])).is_true()


@behaves_like(a_runner, a_serial_runner)
def describe_docker_runner():

    @pytest.fixture(scope='function')
    def cn_fixture():
        return create_autospec(Container, spec_set=True)

    @pytest.fixture(scope='function')
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
            cn_fixture.execute.assert_called_once_with(expected_command)

    def describe_run_all_container_behavior():

        def expect_cn_passed_to_task(cn_fixture, task_fixture):
            docker_mock = create_autospec(DockerClient, spec_set=True)
            expected_command = 'test cmd'
            task_fixture.name = expected_command

            subject = DockerRunner('foo_image', docker=docker_mock, cn=cn_fixture)

            subject.run_all([task_fixture])
            task_fixture.execute.assert_called_once_with(cn=mock.ANY)
