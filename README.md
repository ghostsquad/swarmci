Swarm CI
========

## Architecture

Requires Docker 1.12 or greater
Requires Consul for service discovery

The basic idea of Swarm CI is to leverage Docker Swarm to run decoupled tasks as part of a build within the swarm using one-time-use docker containers (think serverless docker like AWS Lambda).

## Getting Started

### Composing a `.swarmci` file

#### Git Repository

First, you'll need to tell SwarmCI a bit about your repository. Repositories requiring authentication are currently not supported natively, though if you build a docker image with SSH private key baked in under the root account, then ssh will work without any extra configurations in the `.swarmci` file.

```
git:
  url: git+https://my.repo/project.git
```

##### Clone Depth
You can customize the clone depth (which defaults 50)

```
git:
  depth: 3
```

#### Build Layers

A `.swarmci` file consists of several layers.

* `Stages` are run sequentially (identified with unique names). Subsequent stages only start if all jobs from a prior stage complete successfully.
* `Jobs` run in parallel (identified with unique names). Each job consists of one or more tasks, and various bits of meta data.
* `Tasks` are run sequentially within a job on a common container.

Each job consists of several pieces of information:

* `image`: the image to be used for all tasks within this job. (Note: this image should be on an available registry for the swarm to pull from), and should have an entrypoint that _does not exit_, because all tasks will run on this container, and expect the container to continue to be running between tasks. This can be either a string or a list. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `clone`: not all jobs need to clone the repo, set this to `False` if you don't need to clone. Default `True`
* `env`: environment variables to be made available for `tasks`, `before_compose`, `after_failure`, and `finally`. This can be dictionary or a list of dictionaries. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `before_compose` (OPTIONAL): tasks to run before running compose. This can be either a string or a list.
* `compose` (OPTIONAL): a [docker compose](https://docs.docker.com/compose/overview/) dictionary in order to launch a multi-container application for testing. This can be either a dictionary or a list of dictionaries. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `task(s)`: This can be either a string or a list.
* `after_failure` (OPTIONAL): this runs if any task task fails. This can be either a string or a list.
* `finally` (OPTIONAL): this runs regardless of result of prior tasks. This can be either a string or a list.

Full Example:

```
stages:
  foo-stage:
    bar-job:
      image: my-ci-python:3.5
      env:
        foo: bar
        hello: world
      clone: False
      before_compose:
        - docker build -t my.registry:5000/baz .
        - docker push my.registry:5000/baz
      compose:
        version: "2"
        services:
          foo:
            image: foo
          bar:
            image: bar
          baz:
            image: baz
      tasks:
        - /bin/echo "this runs first"
        - python -m pytest tests/
      after_failure: /bin/echo "this runs if any script task fails"
      finally: /bin/echo "this runs regardless of the result of the script tasks"
```

#### <a name="job-matrix"></a>Job Matrix

When a job is converted to a job-matrix, you get all possible combinations of `image`, `env` variables, `compose` definitions and `tasks`. Here is an example job matrix that expands to 120 individual (5 \* 4 \* 3 \* 2) jobs.

```
bar-job:
  image:
    - my-ci-python:2.7
    - my-ci-python:3.2
    - my-ci-python:3.3
    - my-ci-python:3.4
    - my-ci-python:3.5
  env:
    - db: mysql
      foo: v1
    - db: mysql
      foo: v2
    - db: redis
      foo: v2
    - db: mongodb
      foo: v2
  compose:
    - version: "2"
      services:
        foo:
          image: foo:1
        bar:
          image: bar:1      
    - version: "2"
      services:
        foo:
          image: foo:2
        bar:
          image: bar:2
  tasks:
    - /bin/bash -c "echo \"using db: ${db} and foo: ${foo}\""
    - python -m pytest tests/
```
