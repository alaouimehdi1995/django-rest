# -*- coding: utf-8 -*-

import time

import serpy
from django_rest.serializers import Serializer
from django_rest.serializers.fields import CharField, IntegerField, MethodField


class NestedDjangoRESTSerializer(Serializer):
    w = IntegerField()
    x = MethodField()
    y = CharField()
    z = IntegerField()

    def get_x(self, obj):
        return obj.x + 10


class ComplexDjangoRESTSerializer(Serializer):
    foo = CharField()
    bar = IntegerField()
    sub = NestedDjangoRESTSerializer()
    subs = NestedDjangoRESTSerializer(many=True)


class NestedSerpySerializer(serpy.Serializer):
    w = serpy.IntField()
    x = serpy.MethodField()
    y = serpy.StrField()
    z = serpy.IntField()

    def get_x(self, obj):
        return obj.x + 10


class ComplexSerpySerializer(serpy.Serializer):
    foo = serpy.StrField()
    bar = serpy.IntField()
    sub = NestedSerpySerializer()
    subs = NestedSerpySerializer(many=True)


class NestedObject(object):
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.w = w
        self.z = z


class ComplexObject(object):
    def __init__(self):
        self.foo = "bar"
        self.bar = 5
        self.sub = NestedObject(w=1000, x=20, y="hello", z=10)
        self.subs = [
            NestedObject(w=1000 * i, x=20 * i, y="hello" * i, z=10 * i)
            for i in range(10)
        ]


def benchmark_function(test_set_length):
    test_set = [ComplexObject() for i in range(test_set_length)]

    # django_rest
    start_time = time.time()
    django_rest_result = ComplexDjangoRESTSerializer(instance=test_set, many=True).data
    django_rest_timing = time.time() - start_time

    # Serpy
    start_time = time.time()
    serpy_result = ComplexSerpySerializer(instance=test_set, many=True).data
    serpy_timing = time.time() - start_time

    assert django_rest_result == serpy_result

    speed_ratio = django_rest_timing / serpy_timing
    assert speed_ratio < 1.1


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
