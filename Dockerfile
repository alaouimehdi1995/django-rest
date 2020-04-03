FROM python:2-alpine

WORKDIR /usr/src/app

COPY ./tests/requirements/requirements.txt .

RUN pip install -r requirements.txt

RUN django-admin startproject testproject .

COPY django-rest testproject/

COPY tests testproject/

ENTRYPOINT pytest .
