FROM python:3.5-alpine

WORKDIR /usr/src/app

RUN pip install pip-tools

COPY ./tests/requirements/requirements.in .

RUN pip-compile --output-file=requirements.txt requirements.in

RUN pip install -r requirements.txt

RUN django-admin startproject testproject .

COPY django_rest ./django_rest

COPY pytest.ini .
COPY tests/tests tests

ENTRYPOINT pytest tests --cov=django_rest --cov-report="html:/usr/src/app/.report/" --show-capture=no -s
# To run benchmark, uncomment one of the following lines:
#ENTRYPOINT pytest tests/serializers/benchmark.py
#ENTRYPOINT pytest tests/decorators/benchmark/benchmark.py
