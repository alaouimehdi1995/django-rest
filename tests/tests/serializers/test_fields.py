# -*- coding: utf-8 -*-

from decimal import Decimal

import pytest
from mock import Mock

from django_rest.serializers import fields
from django_rest.serializers.exceptions import SerializationError


def test_to_value_method_of_base_field_should_return_its_input():
    assert fields.Field().to_value(5) == 5
    assert fields.Field().to_value("a") == "a"
    assert fields.Field().to_value(None) is None


def test_as_getter_method_of_base_field_should_return_none():
    assert fields.Field().as_getter(None, None) is None


def test_is_to_value_overridden_for_base_field_should_be_false():
    field = fields.Field()
    assert field._is_to_value_overridden() is False


def test_is_to_value_overridden_for_integer_field_should_be_true():
    field = fields.IntegerField()
    field._is_to_value_overridden() is True


def test_is_to_value_overridden_for_custom_field_should_be_true():
    class TransField(fields.Field):
        def to_value(self, value):
            return value

    field = TransField()
    field._is_to_value_overridden() is True


def test_char_field_to_value_method():
    field = fields.CharField()
    assert field.to_value("a") == "a"
    assert field.to_value(5) == "5"


def test_boolean_field_to_value_method():
    field = fields.BooleanField()
    assert field.to_value(True) is True
    assert field.to_value(False) is False
    assert field.to_value(1) is True
    assert field.to_value(0) is False


def test_integer_field_to_value_method():
    field = fields.IntegerField()
    assert field.to_value(5) == 5
    assert field.to_value(5.4) == 5
    assert field.to_value("5") == 5


def test_float_field():
    field = fields.FloatField()
    assert field.to_value(5.2) == 5.2
    assert field.to_value("5.5") == 5.5
    assert field.to_value(Decimal("5.5")) == 5.5


def test_method_field():
    class FakeSerializer(object):
        def get_a(self, obj):
            return obj.a

        def z_sub_1(self, obj):
            return obj.z - 1

    serializer = FakeSerializer()

    assert fields.MethodField.getter_needs_serializer_as_arg is True

    fn = fields.MethodField().as_getter("a", serializer)
    assert fn(Mock(a=3)) == 3

    fn = fields.MethodField(method_name="z_sub_1").as_getter("whatever", serializer)
    assert fn(Mock(z=3)) == 2


def test_constant_field():
    fn = fields.ConstantField(1.3).as_getter("whatever", Mock())
    assert fn(Mock()) == 1.3

    fn = fields.ConstantField().as_getter("whatever", Mock())
    assert fn(Mock()) == None

    fn = fields.ConstantField(constant=[1.3, True]).as_getter("whatever", Mock())
    assert fn(Mock()) == [1.3, True]

    fn = fields.ConstantField(Mock(), required=False).as_getter("whatever", Mock())
    with pytest.raises(TypeError):
        fn(Mock())

    with pytest.raises(SerializationError):
        fields.ConstantField(Mock(), required=True).as_getter("whatever", Mock())


def test_list_field():
    assert fields.ListField(fields.IntegerField()).to_value([]) == []
    assert fields.ListField(fields.IntegerField()).to_value([5]) == [5]
    assert fields.ListField(fields.IntegerField()).to_value(["5"]) == [5]
    assert fields.ListField(fields.IntegerField()).to_value([5.3, "4", 3]) == [5, 4, 3]
    with pytest.raises(TypeError):
        assert fields.ListField(fields.IntegerField()).to_value(5)
