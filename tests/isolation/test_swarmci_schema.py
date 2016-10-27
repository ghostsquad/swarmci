# coding=utf-8
import yaml
import pytest
import jsonschema
from swarmci.swarmci_schema import SCHEMA, stages_schema, stage_schema, jobs_schema, job_schema, commands_schema, command_schema
from assertpy import assert_that
from pytest_describe import behaves_like

# shared fixtures


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


@pytest.fixture(scope='module')
def nameless_input():
    return {}


@pytest.fixture(scope='module')
def bad_subtasks_input():
    return 'foo'

# helper functions


def run_validation(test_input, schema):
    jsonschema.validate(test_input, schema)


def assert_validation_failed(test_input, schema, *extra_matches):
    with pytest.raises(jsonschema.exceptions.ValidationError) as exc_info:
        run_validation(test_input, schema)

    exc_str = str(exc_info.value)
    assert_that(exc_str).matches('Failed validating')

    for extra_match in extra_matches:
        assert_that(exc_str).matches(extra_match)

# shared behaviors


def a_named_task():
    def when_does_not_contain_name_property():
        def expect_json_schema_validation_error(nameless_input, schema):
            assert_validation_failed(nameless_input, schema, "'name' is a required property")


def a_task_with_subtasks():
    def when_not_a_list():
        def expect_json_schema_validation_error(bad_subtasks_input, schema):
            assert_validation_failed(bad_subtasks_input, schema, "'foo' is not of type 'array'")


def a_set_of_commands():
    @pytest.mark.parametrize("test_input", [
        ["foo", "bar"],
        "foo"
    ])
    def expect_strings_and_lists_to_be_valid(test_input, schema):
        run_validation(test_input, schema)

# tests


def describe_full_schema():
    def given_basic_minimum():
        def expect_it_to_be_valid(test_input):
            run_validation(test_input, SCHEMA)


@behaves_like(a_task_with_subtasks)
def describe_stages_schema():
    @pytest.fixture(scope='module')
    def schema():
        return stages_schema


@behaves_like(a_named_task)
def describe_stage_schema():
    @pytest.fixture(scope='module')
    def schema():
        return stage_schema


@behaves_like(a_task_with_subtasks)
def describe_jobs_schema():
    @pytest.fixture(scope='module')
    def schema():
        return jobs_schema


@behaves_like(a_named_task)
def describe_job_schema():
    @pytest.fixture(scope='module')
    def schema():
        return job_schema


@behaves_like(a_set_of_commands)
def describe_commands_schema():
    @pytest.fixture(scope='module')
    def schema():
        return commands_schema


def describe_command_schema():
    @pytest.fixture(scope='module')
    def schema():
        return command_schema

    def given_a_string():
        def when_not_empty():
            def expect_it_to_be_valid(schema):
                run_validation('my command', schema)

        def when_empty():
            def expect_json_schema_validation_error(schema):
                assert_validation_failed("", schema, "Failed validating 'minLength' in schema", "'' is too short")
