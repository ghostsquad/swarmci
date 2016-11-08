import sys
from contextlib import contextmanager
from io import StringIO
from mock import Mock, create_autospec

import pytest
from assertpy import assert_that

from swarmci import parse_args, decide_build_success
from swarmci.task import Task


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
        def when_option_provided():
            def expect_value_passed():
                expected_filename = 'foo.bar'
                actual_args = parse_args(['--file', expected_filename])
                assert_that(actual_args.file).is_equal_to(expected_filename)

        def when_option_not_provided():
            def expect_defaults_to_dot_swarmci():
                actual_args = parse_args([])
                assert_that(actual_args.file).is_equal_to('.swarmci')

    def describe_option_debug():
        def when_debug_flag_provided():
            def expect_debug_set_to_true():
                actual_args = parse_args(['--debug'])
                assert_that(actual_args.debug).is_true()

        def when_debug_flag_not_provided():
            def expect_debug_set_to_false():
                actual_args = parse_args([])
                assert_that(actual_args.debug).is_false()


def describe_decide_build_success():
    def when_task_successful():
        def expect_success_arg_returned():
            task = create_autospec(Task)
            task.successful = True

            expected = Mock()

            result = decide_build_success(task, success=expected, fail=None)

            assert_that(result).is_equal_to(expected)

    def when_task_not_successful():
        def expect_fail_arg_returned():
            task = create_autospec(Task)
            task.successful = False

            expected = Mock()

            result = decide_build_success(task, success=None, fail=expected)

            assert_that(result).is_equal_to(expected)
