import yaml
from swarmci.exceptions import BuildAgentException
from swarmci import Stage


def create_stages(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.load(f)

    _stages = data.get('stages', None)
    if _stages is None:
        raise BuildAgentException('[stages] key not found in yaml file!')

    if type(_stages) is not list:
        raise BuildAgentException('[stages] should be a list in the yaml file!')

    stages = []
    for _stage in _stages:
        stage_name = list(_stage)[0]
        jobs = _stage[stage_name]
        st = Stage(name=stage_name, jobs=jobs)
        stages.append(st)

    return stages
