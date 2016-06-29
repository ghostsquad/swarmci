import os
import yaml
import pytest
from tests import RESOURCES_ROOT

example_yaml_path = os.path.join(RESOURCES_ROOT, 'agents/build/example.yaml')


@pytest.fixture(scope="session")
def example_yaml():
    with open(example_yaml_path, 'r') as f:
        return yaml.load(f)