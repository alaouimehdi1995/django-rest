FROM python:2-alpine

WORKDIR /usr/src/app

COPY ./tests/requirements/requirements.txt .

RUN pip install -r requirements.txt

RUN django-admin startproject testproject .

COPY django_rest ./django_rest

COPY pytest.ini .
COPY tests/tests tests

ENTRYPOINT pytest .
