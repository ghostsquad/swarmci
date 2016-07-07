from assertpy import assert_that
from job import Job


def test_split_given_multiple_images_expect_job_multiplied_by_images():
    """
    A job can be broken a matrix of jobs (permutations).
    Providing multiple images will cause the job to multiply into
    several jobs (1 per image provided)
    """
    test_job = Job(name='my_job', images=['my_image1', 'my_image2'], tasks=['foo', 'bar'])
    result = test_job.split()

    assert_that(result).is_iterable().is_length(2)
    assert_that(result[0].images).is_length(1)
    assert_that(result[1].images).is_length(1)

    actual_images = []
    for r in result:
        for i in r.images:
            actual_images.append(i)

    assert_that(actual_images).contains('my_image1', 'my_image2')


def test_split_given_multiple_env_sets_expect_job_multiplied_by_env_sets():
    """
    A job can be broken a matrix of jobs (permutations).
    Providing multiple env variable sets will cause the job to multiply into
    several jobs (1 per env set provided)
    """
    env_sets = [
        {
            'foo': 'bar'
        },
        {
            'hello': 'world'
        }
    ]
    test_job = Job(name='my_job', images=['my_image1'], env=env_sets, tasks=['foo', 'bar'])
    assert_that(test_job.env).is_type_of(list)
    result = test_job.split()

    assert_that(result).is_iterable().is_length(2)
    assert_that(result[0].env).is_type_of(dict)
    assert_that(result[0].env).is_length(1)

    actual_env_keys = []
    for r in result:
        for k in r.env:
            actual_env_keys.append(k)

    assert_that(actual_env_keys).contains('foo', 'hello')


def test_split_given_single_image_single_env_set_expect_single_job_returned():
    """jobs should only be split with env sets and images"""
    test_job = Job(name='my_job', images=['my_image1'], tasks=['foo', 'bar'])
    result = test_job.split()

    assert_that(result).is_iterable().is_length(1)
    assert_that(result[0].images).is_length(1)

    actual_images = []
    for r in result:
        for i in r.images:
            actual_images.append(i)

    assert_that(actual_images).contains('my_image1')
