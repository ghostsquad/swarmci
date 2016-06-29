import requests
import requests_mock
import pytest

publish_url = "mock://test.com"


@pytest.fixture(scope='function')
def mock_adapter():
    session = requests.Session()
    adapter = requests_mock.Adapter()
    session.mount('mock', adapter)
    adapter.register_uri('POST', publish_url, headers={'Content-Type': 'application/json'})

    return adapter

# adapter.register_uri('GET', 'mock://test.com', text='data')
# resp = session.get('mock://test.com')
# resp.status_code, resp.text
# (200, 'data')


def test_run_stages_given_multiple_jobs_expect_jobs_from_current_stage_only_published():
    raise NotImplementedError


def test_run_stages_given_complete_stage_expect_jobs_from_next_stage_published():
    raise NotImplementedError


def test_run_stages_given_failed_stage_expect_new_jobs_not_published():
    raise NotImplementedError


def test_publish_job_given_job_expect_job_published_to_coordinator():
    raise NotImplementedError


def test_receive_job_given_unfinished_job_logs_output():
    raise NotImplementedError
