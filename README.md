Swarm CI
========

The basic idea of Swarm CI is to leverage Docker Swarm to run builds and tests within containers in an easy, distributed, parallel and fast way.

## Getting Started

### Composing a `.swarmci` file

#### Build Layers

A `.swarmci` file consists of several layers.

* `Stages` are run sequentially (identified with unique names). Subsequent stages only start if all jobs from a prior stage complete successfully.
* `Jobs` run in parallel (identified with unique names). Each job consists of one or more tasks, and various bits of meta data.
* `Tasks` are run sequentially within a job on a common container.

Each job consists of several pieces of information:

* `image(s)` **(required)**: the image to be used for all tasks within this job. This image should be on an available registry for the swarm to pull from (or be built using the `build` task). It should not have an entrypoint, as we'll want to execute an infinite sleep shell command so that it _does not exit_, because all tasks will run on this container, and SwarmCI expects to be able to launch the container, leave it running, and exec tasks on the running container. This can be either a string or a list. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `env` _(optional)_: environment variables to be made available for `tasks`, `before_compose`, `after_failure`, and `finally`. This can be dictionary or a list of dictionaries. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `build` _(optional)_: Similar to the [docker compose build](https://docs.docker.com/compose/compose-file/#build). The SwarmCI agent can build and run the docker image locally before running tasks. The name of the built image will be that of the `image` key within the job. If the `image` job data is a list, it will not be possible to determine what name should be used to build, therefore, you
* `task(s)` **(required)**: This can be either a string or a list. If any task in the list fails, subsequent tasks will not be run, however, `after_failure` and `finally` will run if defined.
* `after_failure` _(optional)_: this runs if any task task fails. This can be either a string or a list.
* `finally` _(optional)_: this runs regardless of result of prior tasks. This can be either a string or a list.

Full Example:

```yaml

stages:
  - my_stage:
    - my_job:
      image: my-ci-python:3.5
      build:
        context: ./docker-dir
        dockerfile: Dockerfile-alternate
        args:
          buildno: 1
      env:
        say_something: hello from 
      tasks:
        - /bin/bash -c 'echo "$say_something $HOSTNAME"'
      after_failure: /bin/echo "this runs if any script task fails"
      finally: /bin/echo "this runs regardless of the result of the script tasks"
    - another_job:
      image: ubuntu
      tasks:
        - /bin/bash -c 'echo "hello again from $HOSTNAME"'
```

#### <a name="job-matrix"></a>Job Matrix

When a job is converted to a job-matrix, you get all possible combinations of `image` and `env` variables. Here is an example job matrix that expands to 6 individual (3 \* 2) jobs.

```yaml
bar-job:
  image:
    - my-ci-python:2.7
    - my-ci-python:3.2
    - my-ci-python:3.5
  env:
    - db: mysql
      foo: v1
    - db: mysql
      foo: v2
  # note: all tasks will run for each expanded job instance
```

## Demo

```
vagrant up
vagrant ssh manager
pushd /vagrant
python setup.py install --force
python swarmci/agent/__init__.py
```

## Running Tests

```
python3.5 runtox.py -e linting,py35,py36
```

or using docker

```
docker build -t swarmci . 
docker build -f Dockerfile.test -t swarmci:test .        
docker run -it swarmci:test
```