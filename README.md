# django-rest

blazing fast django rest library

How to run tests ?
In the root project, run the following commands:

```
docker build . -t django-rest:test
docker container run -ti -v "$PWD/.report:/usr/src/app/.report" django-rest:test
```

How to run coverage inside the docker container ?

```
pytest --cov=django_rest tests --show-capture=no
```
