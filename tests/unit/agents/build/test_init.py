from assertpy import assert_that
from swarmci import Stage
from tests.conftest import example_yaml_path
import swarmci.agents.build as build_agent


def test_create_stages_given_yaml_expect_stages_list_output():
    stages = build_agent.create_stages(example_yaml_path)

    assert_that(stages).is_type_of(list)
    assert_that(stages).is_length(2)
    assert_that(stages[0]).is_type_of(Stage)
