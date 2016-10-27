# coding=utf-8
import yaml
import pytest
import jsonschema
from swarmci.swarmci_schema import SCHEMA
from assertpy import assert_that
from pytest_describe import behaves_like


@pytest.fixture
def test_input():
    document = """
      stages:
          - name: foo_stage
            jobs:
                - name: foo_job
                  commands: test command
    """
    return yaml.load(document)


def run_validation(test_input):
    jsonschema.validate(test_input, SCHEMA)


def assert_validation_failed(test_input, extra_match):
    with pytest.raises(jsonschema.exceptions.ValidationError) as exc_info:
        run_validation(test_input)

    exc_str = str(exc_info.value)
    assert_that(exc_str).matches('Failed validating')
    if extra_match:
        assert_that(exc_str).matches(extra_match)


def given_basic_minimum():
    def expect_it_to_be_valid(test_input):
        run_validation(test_input)


def describe_stages():
    def given_stages_not_a_list():
        def expect_json_schema_validation_error(test_input):
            test_input['stages'] = 'foo'
            assert_validation_failed(test_input, "'foo' is not of type 'array'")


def describe_stage():
    def when_does_not_contain_name_property():
        def expect_json_schema_validation_error(test_input):
            del test_input['stages'][0]['name']
            assert_validation_failed(test_input, "'name' is a required property")


def describe_jobs():
    def given_jobs_not_a_list():
        def expect_json_schema_validation_error(test_input):
            test_input['stages'][0]['jobs'] = 'foo'
            assert_validation_failed(test_input, "'foo' is not of type 'array'")


def describe_job():
    def when_does_not_contain_name_property():
        def expect_json_schema_validation_error(test_input):
            del test_input['stages'][0]['name']
            assert_validation_failed(test_input, "'name' is a required property")