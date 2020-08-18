# -*- coding: utf-8 -*-

import json
import django
import time

from django.test.client import RequestFactory

from ..common import payload
from ..drf_view import drf_view
from ..django_rest_view import django_rest_view

_OUTPUT_CSV_PATH = "/usr/src/app/.report/e2e_benchmark.csv"


# The Request object

request = RequestFactory().post(
    "/whatever/", data=json.dumps(payload), content_type="application/json"
)


def get_functions_timings(sample_length):

    # django_rest lib
    start_time = time.time()
    for i in range(sample_length):
        django_rest_response = django_rest_view(request).content.decode()
    django_rest_timing = time.time() - start_time

    # DjangoRESTFramework
    start_time = time.time()
    for i in range(sample_length):
        drf_response = drf_view(request).render().content.decode()
    drf_timing = time.time() - start_time

    # Comparing results
    django_rest_result = json.loads(django_rest_response)
    drf_result = json.loads(drf_response)
    # assert django_rest_response.status_code == 200
    # assert drf_response.status_code == 200
    assert django_rest_result == drf_result

    return django_rest_timing, drf_timing


def benchmark_average_timings(sample_length):
    repetitions = 10
    total_django_rest_timings = 0
    total_drf_timings = 0
    for i in range(repetitions):
        django_rest_timing, drf_timing = get_functions_timings(sample_length)
        total_django_rest_timings += django_rest_timing
        total_drf_timings += drf_timing

    avg_django_rest_timing = total_django_rest_timings / repetitions
    avg_drf_timing = total_drf_timings / repetitions
    return avg_django_rest_timing, avg_drf_timing


def run_benchmark():
    sample_lengths = [10, 50, 100, 500, 1000, 5000, 10000]
    django_rest_timings = []
    drf_timings = []
    for sample_length in sample_lengths:
        django_rest_avg_timing, drf_avg_timing = benchmark_average_timings(
            sample_length
        )
        django_rest_timings.append(django_rest_avg_timing)
        drf_timings.append(drf_avg_timing)

    data_matrix = [["# of requests", "django-REST", "Django REST Framework"]] + [
        [sample_lengths[i], django_rest_timings[i], drf_timings[i]]
        for i in range(len(sample_lengths))
    ]
    export_data_into_csv(_OUTPUT_CSV_PATH, data_matrix)


def export_data_into_csv(csv_filepath, data_matrix):
    with open(csv_filepath, "w") as f:
        for row in data_matrix:
            str_row = (str(e) for e in row)
            f.write("{}\n".format(",".join(str_row)))


if __name__ == "__main__":
    django.setup()
    run_benchmark()
