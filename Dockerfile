FROM python:3.5-alpine

RUN apk update && apk add g++

WORKDIR /usr/src/app

RUN pip install pip-tools

COPY ./tests/requirements/requirements.in .

RUN pip-compile --output-file=requirements.txt requirements.in

RUN pip install -r requirements.txt

RUN django-admin startproject testproject .

COPY django_rest ./django_rest

COPY pytest.ini .
COPY tests/tests tests
COPY tests/benchmarks ./benchmarks

#ENTRYPOINT pytest tests --cov=django_rest --cov-report="html:/usr/src/app/.report/" --show-capture=no -s
# To run benchmark, uncomment one of the following lines:
#ENTRYPOINT pytest tests/serializers/benchmark.py
#ENTRYPOINT python benchmarks/scripts/e2e.py
ENV DJANGO_SETTINGS_MODULE 'testproject.settings'
ENTRYPOINT python -m benchmarks.scripts.e2e
#ENTRYPOINT python -m benchmarks.scripts.serializers
#ENTRYPOINT python -m benchmarks.scripts.deserializers
#ENTRYPOINT python -m benchmarks.scripts.empty_view
