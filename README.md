Swarm CI
========

## Architecture

* Requires Docker 1.12 or greater
* Requires Consul for service discovery

The basic idea of Swarm CI is to leverage Docker Swarm to run builds and tests within containers in an easy, distributed, parallel and fast way.

## Getting Started

### Composing a `.swarmci` file

#### Git Repository

First, you'll need to tell SwarmCI a bit about your repository. Repositories requiring authentication are currently not supported natively, though if you build a docker image with SSH private key baked in under the root account, then ssh will work without any extra configurations in the `.swarmci` file.

```yaml
git:
  url: git+https://my.repo/project.git
```

##### Clone Depth
You can customize the clone depth (which defaults 50)

```yaml
git:
  depth: 3
```

#### Build Layers

A `.swarmci` file consists of several layers.

* `Stages` are run sequentially (identified with unique names). Subsequent stages only start if all jobs from a prior stage complete successfully.
* `Jobs` run in parallel (identified with unique names). Each job consists of one or more tasks, and various bits of meta data.
* `Tasks` are run sequentially within a job on a common container.

Each job consists of several pieces of information:

* `image(s)` **(required)**: the image to be used for all tasks within this job. This image should be on an available registry for the swarm to pull from (or be built using the `build` task), and should have an entrypoint that _does not exit_, because all tasks will run on this container, and SwarmCI expects to be able to launch the container, leave it running, and exec tasks on the running container. This can be either a string or a list. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `clone` _(optional)_: not all jobs need to clone the repo, set this to `False` if you don't need to clone. Default `True`
* `env` _(optional)_: environment variables to be made available for `tasks`, `before_compose`, `after_failure`, and `finally`. This can be dictionary or a list of dictionaries. When in list form, this job will be converted to a [job matrix](#job-matrix).
* `build` _(optional)_: Similar to the [docker compose build](https://docs.docker.com/compose/compose-file/#build). The SwarmCI agent can build and run the docker image locally before running tasks. The name of the built image will be that of the `image` key within the job. If the `image` job data is a list, it will not be possible to determine what name should be used to build, therefore, you
* `task(s)` **(required)**: This can be either a string or a list. If any task in the list fails, subsequent tasks will not be run, however, `after_failure` and `finally` will run if defined.
* `after_failure` _(optional)_: this runs if any task task fails. This can be either a string or a list.
* `finally` _(optional)_: this runs regardless of result of prior tasks. This can be either a string or a list.

Full Example:

```yaml
stages:
  - foo-stage:
      bar-job:
        image: my-ci-python:3.5
        build:
          context: ./docker-dir
          dockerfile: Dockerfile-alternate
          args:
            buildno: 1
        env:
          foo: bar
          hello: world
        clone: False
        tasks:
          - /bin/echo "this runs first"
          - python -m pytest tests/
        after_failure: /bin/echo "this runs if any script task fails"
        finally: /bin/echo "this runs regardless of the result of the script tasks"
  - bar-stage:
      job1:
         image: foo
         task: /bin/echo "hello world"

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
