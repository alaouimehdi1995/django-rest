# -*- coding: utf-8 -*-

from django.http import JsonResponse

from django_rest.decorators import api_view
from django_rest.deserializers import fields as deserializers_fields, Deserializer
from django_rest.serializers import fields as serializers_fields, Serializer

from .common import ComplexObject

#  === Serializers


class DjangoRESTSimpleSerializer(Serializer):
    w = serializers_fields.IntegerField()
    x = serializers_fields.MethodField()
    y = serializers_fields.CharField()
    z = serializers_fields.IntegerField()

    def get_x(self, obj):
        return obj.x + 10


class DjangoRESTComplexSerializer(Serializer):
    foo = serializers_fields.CharField()
    bar = serializers_fields.IntegerField()
    sub = DjangoRESTSimpleSerializer()
    subs = DjangoRESTSimpleSerializer(many=True)


#  === Deserializers


class DjangoRESTSimpleDeserializer(Deserializer):
    w = deserializers_fields.IntegerField()
    x = deserializers_fields.IntegerField()
    y = deserializers_fields.CharField()
    z = deserializers_fields.IntegerField()


class DjangoRESTComplexDeserializer(Deserializer):
    foo = deserializers_fields.CharField()
    bar = deserializers_fields.IntegerField()
    #sub = DjangoRESTSimpleDeserializer()


@api_view(deserializer_class=DjangoRESTComplexDeserializer)
def django_rest_view(request, url_params, query_params, deserialized_data):
    complex_object = ComplexObject(**deserialized_data)
    serialized_data = DjangoRESTComplexSerializer(instance=complex_object).data
    return JsonResponse(serialized_data)
