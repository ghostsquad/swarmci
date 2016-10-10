import pytest
from contextlib import contextmanager
from io import StringIO
import sys
from assertpy import assert_that
from swarmci import parse_args
from swarmci.errors import SwarmCIError
from swarmci import build_tasks_hierarchy
from swarmci.task import Task, TaskType, TaskFactory


def describe_build_tasks_hierarchy():
    def given_no_stages():
        def expect_error_raised():
            config = {
                "foo": "bar"
            }

            with pytest.raises(SwarmCIError) as excinfo:
                build_tasks_hierarchy(config, TaskFactory())

            assert_that(str(excinfo.value)).is_equal_to('Did not find "stages" key in the .swarmci file.')

    def given_stages_not_a_list():
        def expect_error_raised():
            config = {
                "stages": "bar"
            }

            with pytest.raises(SwarmCIError) as excinfo:
                build_tasks_hierarchy(config, TaskFactory())

            assert_that(str(excinfo.value)).is_equal_to(
                'The value of the "stages" key should be a list in the .swarmci file.')

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
        task = build_tasks_hierarchy(config, TaskFactory())

        assert_that(task).is_instance_of(Task)
        assert_that(task.task_type).is_equal_to(TaskType.BUILD)


@contextmanager
def capture_sys_output():
    capture_out, capture_err = StringIO(), StringIO()
    current_out, current_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = capture_out, capture_err
        yield capture_out, capture_err
    finally:
        sys.stdout, sys.stderr = current_out, current_err


def describe_parse_args():
    def given_version_option():
        def expect_package_and_version_returned():
            with pytest.raises(SystemExit):
                with capture_sys_output() as (stdout, stderr):
                    parse_args(['--version'])

            assert_that(stdout.getvalue()).matches(r'SwarmCI \d+\.\d+\.\d+')

    def given_file_option():
        def expect_file_set_in_output():
            expected_filename = 'foo.bar'
            actual_args = parse_args(['--file', expected_filename])
            assert_that(actual_args.file).is_equal_to(expected_filename)
