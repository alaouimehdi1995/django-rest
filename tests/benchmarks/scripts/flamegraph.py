# -*- coding: utf-8 -*-

import json
import django

from django.test.client import RequestFactory

from ..common import payload
from ..drf_view import drf_view
from ..django_rest_view import django_rest_view
from ..flamegraph_sampler import Sampler

REPETITIONS = 10000
DJANGO_REST_FLAMEGRAPH_OUTPUT_PATH = "/usr/src/app/.report/django_rest_flamegraph.svg"
DRF_FLAMEGRAPH_OUTPUT_PATH = "/usr/src/app/.report/drf_flamegraph.svg"
sampler = Sampler(interval=0.0001)


# The Request object

request = RequestFactory().post(
    "/whatever/", data=json.dumps(payload), content_type="application/json"
)

if __name__ == "__main__":
    django.setup()
    django_rest_response = django_rest_view(request)

    # Django-REST
    sampler.start()
    for i in range(REPETITIONS):
        django_rest_response = django_rest_view(request)
    with open(DJANGO_REST_FLAMEGRAPH_OUTPUT_PATH, "w") as f:
        f.write(sampler.output_stats())

    # Django-REST Framework
    sampler.restart()
    for i in range(REPETITIONS):
        django_rest_response = drf_view(request).render()
    with open(DRF_FLAMEGRAPH_OUTPUT_PATH, "w") as f:
        f.write(sampler.output_stats())
