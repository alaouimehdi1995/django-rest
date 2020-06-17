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


# def test_benchmark_decorators():
def benchmark_function(test_set_length):

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
    django_rest_result = json.loads(django_rest_response.content)
    drf_result = json.loads(drf_response.content)
    assert django_rest_response.status_code == 200
    assert drf_response.status_code == 200
    assert django_rest_result == drf_result

    speed_ratio = django_rest_timing / drf_timing
    assert speed_ratio < 0.1


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
