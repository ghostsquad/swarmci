import pytest
from assertpy import assert_that
from swarmci.exceptions import SwarmCIException
from swarmci import build_tasks_hierarchy
from swarmci.task import TaskFactory


def describe_get_build_hierarchy():
    def given_no_stages():
        def expect_error_raised():
            config = {
                "foo": "bar"
            }

            with pytest.raises(SwarmCIException) as excinfo:
                build_tasks_hierarchy(config, TaskFactory())

            assert_that(str(excinfo.value)).is_equal_to('Did not find "stages" key in the .swarmci file.')

    def given_stages_not_a_list():
        def expect_error_raised():
            config = {
                "stages": "bar"
            }

            with pytest.raises(SwarmCIException) as excinfo:
                build_tasks_hierarchy(config, TaskFactory())

            assert_that(str(excinfo.value)).is_equal_to(
                'The value of the "stages" key should be a list in the .swarmci file.')
