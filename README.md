SwarmCI - Build Your Code in the Swarm
======================================

![Build Status](https://travis-ci.org/ghostsquad/swarmci.svg?branch=master) ![Coveralls](https://coveralls.io/repos/github/ghostsquad/swarmci/badge.svg?branch=master) [![codecov](https://codecov.io/gh/ghostsquad/swarmci/branch/master/graph/badge.svg)](https://codecov.io/gh/ghostsquad/swarmci)

SwarmCI (super pre-alpha) is a CI extension, meaning, you can use it to extend your existing build system (jenkins, bamboo, teamcity, etc), with parallel, distributed, isolated build tasks by leveraging your Docker Swarm.

[![Demo Video](https://img.youtube.com/vi/Vkcnyc17HVI/0.jpg)](https://www.youtube.com/watch?v=Vkcnyc17HVI)

## Inspiration
This project inspired me because of the problems I've faced with conventional CI platforms like Jenkins, Bamboo, Teamcity.

### Problems with Local platforms (Bamboo, Teamcity and Jenkins, ...)

1. Agents have no isolation from the build tasks, sometimes causing hard to reproduce issues involving subprocesses and limitations of the build agent.
2. Agent VM/Containers need to be customized with differing capabilities (SDKs, versions, libraries, resources like cpu/mem, etc). 
    * This requires either an Ops team to maintain the permutations of build capabilities, or
    * Requires each build to install it's dependencies at build time, resulting in longer build times
3. Build <-> Agent binding (when your build needs specific things pre-installed), is wasteful as you must wait for an idle agent that meets the build requirements before the build will run.
3. Builds often write files to disk, and spin up processes, which don't always get reliably cleaned up. These changes between builds can cause unexpected failures or false-successes.
4. Adding parallelism to your build pipeline requires licensing and additional VMs per agent. Expensive!
5. Build agents are often underutilized, either idle, or running builds with low system requirements.

### Problems with Online Platforms (TravisCI, CircleCI, CodeShip, ...)

1. Base images/os availability is limited. With SwarmCI, you can choose your base image, pre-loaded with whatever dependencies you need, meaning you'll have fewer setup/dependency steps and faster, simpler builds.
2. Discovering the bottlenecks, throttling, or transient failures may be quite difficult.
3. Cost can still be significantly reduced, as an example, by putting your Docker Swarm on AWS Spot Instances.

## What it does
You can use SwarmCI to extend an existing CI system (Bamboo, TeamCity, Jenkins, etc) with a few steps.

1. Setup a Docker Swarm.
2. Converting existing build tasks, stages, and jobs to a single `.swarmci` file.
3. Configure a single task in your build to run a single command to delegate work to your Docker Swarm:

`python -m swarmci`

## Getting Started

### Composing a `.swarmci` file

#### Build Layers

A `.swarmci` file consists of several layers.

* `Stages` are run sequentially (identified with unique names). Subsequent stages only start if all jobs from a prior stage complete successfully.
* `Jobs` run in parallel (identified with unique names). Each job consists of one or more commands, and various bits of meta data.
* `Commands` are run sequentially within a job on a common container.

Each job consists of several pieces of information:

* `image(s)` **(required)**: the image to be used for all tasks within this job. This image should be on an available registry for the swarm to pull from (or be built using the `build` task). It should not have an entrypoint, as we'll want to execute an infinite sleep shell command so that it _does not exit_, because all tasks will run on this container, and SwarmCI expects to be able to launch the container, leave it running, and exec tasks on the running container. ~~This can be either a string or a list. When in list form, this job will be converted to a [job matrix](#job-matrix).~~
* `env` _(optional)_: environment variables to be made available for `commands`, `after_failure`, and `finally_command`. This can be dictionary or a list of dictionaries. ~~When in list form, this job will be converted to a [job matrix](#job-matrix).~~
* TODO: `build` _(optional)_: Similar to the [docker compose build](https://docs.docker.com/compose/compose-file/#build). The SwarmCI agent can build and run the docker image locally before running tasks. The name of the built image will be that of the `image` key within the job.
* `commands` **(required)**: This can be either a string or a list. If any command fails, subsequent commands will not be run, however, `after_failure` and `finally_command` will run if defined.
* `after_failure` _(optional)_: this runs if any command fails. This can be either a string or a list.
* `finally_command(s)` _(optional)_: This can be either a string or a list. This runs regardless of result of prior commands.

Full Example:

```yaml
stages:
  - name: my first stage
    jobs:
    - name: my_job
      image: python:alpine
      env:
        say_something: hello from
      commands:
        - /bin/sh -c 'echo "$say_something $HOSTNAME"'
        - /bin/sh -c 'echo "second task within my_job in $HOSTNAME"'
      after_failure_command: /bin/echo "this runs if any script task fails"
      finally_command: /bin/echo "this runs regardless of the result of the script tasks"
    - name: another_job
      image: python:alpine
      commands:
        - /bin/sh -c 'echo "another_job says hello from $HOSTNAME"'
  - name: my second stage
    jobs:
    - name: default_job_in_second_stage
      image: python:alpine
      commands:
        - /bin/sh -c 'echo "look my, second stage job running in $HOSTNAME"'

```

#### <a name="job-matrix"></a>TODO: Job Matrix

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
/opt/swarmci/run-demo.sh
```

## Running Tests

```
pip install tox
tox
```

or using docker

```
docker build -t swarmci . 
docker build -f Dockerfile.test -t swarmci:test .        
docker run -it swarmci:test
```

## RoadMap

### Immediate

- Improved CLI
  - The output is very hard to read with jobs run in parallel
  - The output in general needs some love.
     - Color output (https://github.com/jkbrzt/httpie#colors-and-formatting)
- User Interface
- API
- Data Persistence

### Later

- Caching (like https://docs.travis-ci.com/user/caching/)
- Docker Builds
- Docker Compose
- Docker Push
- Secrets Management (For private repositories)
- Automatic Git Cloning (requires the secrets management above)
- Job Matrix (like https://docs.travis-ci.com/user/customizing-the-build/#Build-Matrix)
- Timeouts
- Manually Started Stages/Jobs
- Build Diff (Compare build output, commits, etc) *This is a feature I haven't seen much anywhere
- Automatic test parallelism (https://circleci.com/docs/test-metadata/)


## Terms Explained

`Stage` - Stages are individual sequential steps. Stages provide a mechanism to break a build into multiple chunks of work such as compilation, testing, and deployment. When a Stage executes, all of the Jobs within that Stage begin executing in parallel, greatly reducing its execution time.

`Job` - Jobs are smaller, independent units of work, which can run in parallel. Each job runs in a separate container. Jobs in subsequent stages will not begin executing until all jobs in the previous stage have completed successfully. A single job failure will result in a failed stage (though it does not cause other jobs to stop running).

`Command` - Commands are literal commands run in a common container with the job in which they are defined, and they run in series. A single command failure (exit_code != 0) will halt a job and mark the job as a failure.
