import pytest
from contextlib import contextmanager
from io import StringIO
import sys
from assertpy import assert_that
from swarmci import parse_args
from swarmci import build_tasks_hierarchy
import swarmci.task


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

        assert_that(task).is_instance_of(swarmci.task.Build)


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
