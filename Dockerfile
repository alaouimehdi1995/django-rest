FROM python:2-alpine

WORKDIR /usr/src/app

COPY ./tests/requirements/requirements.txt .

RUN pip install -r requirements.txt

RUN django-admin startproject testproject .

COPY flash_rest ./flash_rest

COPY pytest.ini .
COPY tests/tests tests

ENTRYPOINT pytest tests --cov=flash_rest --cov-report="html:/usr/src/app/.report/" --show-capture=no -s
# To run benchmark, uncomment the following line:
#ENTRYPOINT pytest tests/serializers/benchmark.py
