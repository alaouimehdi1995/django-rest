# -*- coding: utf-8 -*-

from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .common import ComplexObject

#  === Serializers


class DRFSimpleSerializer(serializers.Serializer):
    w = serializers.FloatField()
    x = serializers.SerializerMethodField()
    y = serializers.CharField()
    z = serializers.IntegerField()

    def get_x(self, obj):
        return obj.x + 10


class DRFComplexSerializer(serializers.Serializer):
    foo = serializers.CharField()
    bar = serializers.IntegerField()
    sub = DRFSimpleSerializer()
    subs = DRFSimpleSerializer(many=True)


#  === Deserializers


class DRFSimpleDeserializer(serializers.Serializer):
    w = serializers.FloatField()
    x = serializers.IntegerField()
    y = serializers.CharField()
    z = serializers.IntegerField()


class DRFComplexDeserializer(serializers.Serializer):
    foo = serializers.CharField()
    bar = serializers.IntegerField()
    sub = DRFSimpleDeserializer()


@api_view(["POST"])
def drf_view(request):
    deserializer = DRFComplexDeserializer(data=request.data)
    deserializer.is_valid()
    validated_data = deserializer.validated_data
    complex_object = ComplexObject(**validated_data)
    serializer = DRFComplexSerializer(complex_object)
    # serializer.is_valid()
    serialized_data = serializer.data
    return Response(serialized_data)
