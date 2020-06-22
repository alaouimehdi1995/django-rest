# -*- coding: utf-8 -*-

import json
import time

from django.test.client import RequestFactory

from .drf_view import drf_view
from .django_rest_view import django_rest_view


# The Request object

payload = {
    "foo": "bar",
    "bar": 5,
    "sub": {"x": 20, "y": "hello", "z": 10, "w": 1000},
}

request = RequestFactory().post(
    "/whatever/", data=json.dumps(payload), content_type="application/json"
)

"""
import cProfile
cProfile.runctx(
    "for i in range(test_set_length): django_rest_view(request)",
    globals={},
    locals={
        "test_set_length": 5000,
        "request": request,
        "django_rest_view": drf_view,
    },
    sort="tottime",
)
"""

# def test_benchmark_decorators():
def benchmark_run_function(test_set_length):

    # django_rest lib
    start_time = time.time()
    for i in range(test_set_length):
        django_rest_response = django_rest_view(request)
    django_rest_timing = time.time() - start_time

    # DjangoRESTFramework
    start_time = time.time()
    for i in range(test_set_length):
        drf_response = drf_view(request).render()
    drf_timing = time.time() - start_time

    # Comparing results
    django_rest_result = json.loads(django_rest_response.content.decode())
    drf_result = json.loads(drf_response.content.decode())
    assert django_rest_response.status_code == 200
    assert drf_response.status_code == 200
    assert django_rest_result == drf_result

    #print()
    #print('N. elements per second: ', test_set_length)
    #print(' - django-REST: ', int(test_set_length/django_rest_timing))
    #print(' - DRF: ', int(test_set_length/drf_timing))

    #speed_ratio = django_rest_timing / drf_timing
    #assert speed_ratio < 0.1
    return django_rest_timing, drf_timing

def benchmark_function(test_set_length):
    repetitions = 10
    total_django_rest_timings = 0
    total_drf_timings = 0
    for i in range(repetitions):
        django_rest_timing, drf_timing = benchmark_run_function(test_set_length)
        total_django_rest_timings += django_rest_timing
        total_drf_timings += drf_timing

    avg_django_rest_timing = total_django_rest_timings/repetitions
    avg_drf_timing = total_drf_timings/repetitions
    print('\n\n')
    print('=========== Benchmark results: ({} elements, {} repetitions) ======================'.format(test_set_length, repetitions))
    print('* Average total timing (sec): (Lower is better)')
    print('*     - django-REST: ', avg_django_rest_timing)
    print('*     - DRF: ', avg_drf_timing)
    print('* Average timing per element (sec): (Lower is better)')
    print('*     - django-REST: ', avg_django_rest_timing/test_set_length)
    print('*     - DRF: ', avg_drf_timing/test_set_length)
    print('* Average Nb of handled requests per second: (Higher is better)')
    print('*     - django-REST: ', int(test_set_length/avg_django_rest_timing))
    print('*     - DRF: ', int(test_set_length/avg_drf_timing))
    print('* Average Perfs ratio:')
    print('*     - django-REST is {} times faster than DRF.'.format(avg_drf_timing/avg_django_rest_timing))
    return avg_django_rest_timing, avg_drf_timing


def test_benchmark():
    test_set = [10, 50, 100, 500, 1000, 5000, 10000]
    django_rest_timings = []
    drf_timings = []
    for i in test_set:
        django_rest_avg_timing, drf_avg_timing = benchmark_function(test_set_length=i)
        django_rest_timings.append(django_rest_avg_timing)
        drf_timings.append(drf_avg_timing)

    import pudb;pudb.set_trace()
    with open('/usr/src/app/.report/benchmark.csv', 'w') as f:
        f.write('{}\n'.format(','.join(['# of requests', 'django-REST', 'DjangoRestFramework'])))
        for i, n in enumerate(test_set):
            f.write('{}\n'.format(','.join([str(n), str(django_rest_timings[i]), str(drf_timings[i])])))



"""
def test_10_elements():
    i = 10
    benchmark_function(test_set_length=i)


def test_100_elements():
    i = 100
    benchmark_function(test_set_length=i)


def test_1000_elements():
    i = 1000
    benchmark_function(test_set_length=i)


def test_10000_elements():
    i = 10000
    benchmark_function(test_set_length=i)


def test_50000_elements():
    i = 50000
    benchmark_function(test_set_length=i)
"""
