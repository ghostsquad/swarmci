from mock import Mock, call, create_autospec
from assertpy import assert_that
import pytest
from docker import Client as DockerClient
from swarmci.docker import Container
from swarmci.errors import DockerCommandFailedError


container_init_defaults = {
    'image': 'test_img',
    'host_config': {},
    'name': 'test_name',
    'env': {},
}


def create_container_obj(docker_client, **kwargs):
    options = container_init_defaults.copy()
    options.update({'docker': docker_client})
    options.update(kwargs)

    return Container(**options)


def describe_container():
    def describe_init():
        def creates_container_from_docker_client():
            expected_image = 'test_img'
            expected_host_config = {}
            expected_name = 'test_name'
            expected_env = {}
            expected_cmd = '/bin/sh -c "while true; do sleep 1000; done"'
            expected_cn_id = '12345'

            docker_mock = create_autospec(DockerClient, spec_set=True)
            docker_mock.create_container.return_value = {'Id': expected_cn_id}

            subject = Container(expected_image,
                                expected_host_config,
                                docker_mock,
                                name=expected_name,
                                env=expected_env)

            docker_mock.create_container\
                .assert_called_once_with(image=expected_image,
                                         host_config=expected_host_config,
                                         name=expected_name,
                                         environment=expected_env,
                                         command=expected_cmd)

            assert_that(subject.id).is_equal_to(expected_cn_id)

        def expect_container_started():
            expected_cn_id = '12345'
            docker_mock = create_autospec(DockerClient, spec_set=True)
            docker_mock.create_container.return_value = {'Id': expected_cn_id}

            create_container_obj(docker_mock)

            docker_mock.start.assert_called_once_with(expected_cn_id)

    def describe__enter__():
        def expect_returns_self():
            options = container_init_defaults.copy()
            options['docker'] = create_autospec(DockerClient, spec_set=True)

            with Container(**options) as cn:
                assert_that(cn).is_instance_of(Container)

    def describe__exit__():
        def given_remove_true():
            def expect_container_removed():
                docker_mock = create_autospec(DockerClient, spec_set=True)

                expected_cn_id = '12345'
                docker_mock.create_container.return_value = {'Id': expected_cn_id}

                options = container_init_defaults.copy()
                options['docker'] = docker_mock
                options['remove'] = True

                with Container(**options):
                    pass

                docker_mock.remove_container.assert_called_once_with(container=expected_cn_id, v=True, force=True)

        def given_remove_false():
            def expect_container_stopped():
                docker_mock = create_autospec(DockerClient, spec_set=True)

                expected_cn_id = '12345'
                docker_mock.create_container.return_value = {'Id': expected_cn_id}

                options = container_init_defaults.copy()
                options['docker'] = docker_mock
                options['remove'] = False

                with Container(**options):
                    pass

                docker_mock.stop.assert_called_once_with(container=expected_cn_id)

    def describe_cp():
        # TODO finish tests for this
        pass

    def describe_execute():

        @pytest.fixture(scope='function')
        def docker_client_fixture():
            docker_mock = create_autospec(DockerClient, spec_set=True)
            expected_cn_id = 'c123'
            docker_mock.create_container.return_value = {'Id': expected_cn_id}

            docker_mock.exec_create.return_value = {'Id': 'e123'}
            docker_mock.exec_start.return_value = []
            docker_mock.exec_inspect.return_value = {'ExitCode': 0}

            return docker_mock

        def expect_docker_exec_created(docker_client_fixture):
            create_container_obj(docker_client_fixture).execute('my_cmd')

            docker_client_fixture.exec_create\
                .assert_called_once_with(container='c123', cmd='my_cmd', tty=True)

        def expect_exec_started(docker_client_fixture):
            create_container_obj(docker_client_fixture).execute('my_cmd')

            docker_client_fixture.exec_start \
                .assert_called_once_with(exec_id='e123', stream=True)

        def expect_out_func_called_for_each_output_line(docker_client_fixture):
            docker_client_fixture.exec_start.return_value = [b'line1', b'line2']
            mock_out_func = Mock()

            create_container_obj(docker_client_fixture).execute('my_cmd', mock_out_func)

            calls = [call('line1'), call('line2')]
            mock_out_func.assert_has_calls(calls)

        def given_exit_code_not_zero():
            def expect_error_raised(docker_client_fixture):
                docker_client_fixture.exec_inspect.return_value = {'ExitCode': 18}

                with pytest.raises(DockerCommandFailedError) as excinfo:
                    create_container_obj(docker_client_fixture).execute('my_cmd')

                assert_that(str(excinfo.value)).is_equal_to('command [my_cmd] returned exitcode [18]')

        def given_exit_code_0():
            def expect_no_error_raised(docker_client_fixture):
                docker_client_fixture.exec_inspect.return_value = {'ExitCode': 0}

                create_container_obj(docker_client_fixture).execute('my_cmd')
