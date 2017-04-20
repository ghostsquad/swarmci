# coding=utf-8
import pytest
from assertpy import assert_that
from swarmci.util import raise_


def describe_raise_():
    def given_exception():
        def expect_exception_raised():
            expected_msg = 'this is a value error'
            with pytest.raises(ValueError) as exc_info:
                raise_(ValueError(expected_msg))

            assert_that(str(exc_info.value)).is_equal_to(expected_msg)
