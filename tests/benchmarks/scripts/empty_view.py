# -*- coding: utf-8 -*-

import json
import django
import time

from django.http import JsonResponse
from django.test.client import RequestFactory
from django_rest.decorators import api_view
from rest_framework.decorators import api_view as drf_api_view
from rest_framework.response import Response

from ..common import payload

_OUTPUT_CSV_PATH = "/usr/src/app/.report/empty_view_benchmark.csv"
# The Request object


request = RequestFactory().post(
    "/whatever/", data=json.dumps(payload), content_type="application/json"
)


@drf_api_view(["POST"])
def drf_view(request):
    return Response({"msg": "Hello world!"})


@api_view
def django_rest_view(request, url_params, query_params, deserialized_data):
    return JsonResponse({"msg": "Hello world!"})


def get_functions_timings(sample_length):

    # django_rest lib
    start_time = time.time()
    for i in range(sample_length):
        django_rest_response = django_rest_view(request)
    django_rest_timing = time.time() - start_time

    # DjangoRESTFramework
    start_time = time.time()
    for i in range(sample_length):
        drf_response = drf_view(request).render()
    drf_timing = time.time() - start_time

    # Comparing results
    django_rest_result = json.loads(django_rest_response.content.decode())
    drf_result = json.loads(drf_response.content.decode())
    assert django_rest_response.status_code == 200
    assert drf_response.status_code == 200
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
