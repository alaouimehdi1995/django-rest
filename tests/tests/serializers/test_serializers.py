# -*- coding: utf-8 -*-

import pytest
from mock import Mock

from django_rest.serializers import DictSerializer, Serializer, fields
from django_rest.serializers.exceptions import SerializationError


def test_simple_serializer():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    a = Mock(a=5)

    # When
    data = ASerializer(a).data

    # Then
    assert data == {"a": 5}


def test_caching_data_in_simple_serializer():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    a = Mock(a=5)

    # When
    serializer = ASerializer(a)
    data1 = serializer.data
    data2 = serializer.data

    # Then
    assert data1 is data2


def test_serializers_inheritance():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    class CSerializer(Serializer):
        c = fields.Field()

    class ABSerializer(ASerializer):
        b = fields.Field()

    class ABCSerializer(ABSerializer, CSerializer):
        pass

    a = Mock(a=5, b="hello", c=100)

    # When
    a_data = ASerializer(a).data
    ab_data = ABSerializer(a).data
    abc_data = ABCSerializer(a).data

    # Then
    assert a_data == {"a": 5}
    assert ab_data == {"a": 5, "b": "hello"}
    assert abc_data == {"a": 5, "b": "hello", "c": 100}


def test_serializing_many_objects():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    objs = [Mock(a=i) for i in range(5)]

    # When
    data = ASerializer(objs, many=True).data

    # Then
    assert len(data) == 5
    assert data == [{"a": 0}, {"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}]


def test_nested_serializers():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    class BSerializer(Serializer):
        b = ASerializer()

    obj = Mock(**{"b.a": 3})

    # When
    data = BSerializer(obj).data

    # Then
    assert data == {"b": {"a": 3}}


def test_nested_serializers_with_many_option():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    class BSerializer(Serializer):
        b = ASerializer(many=True)

    obj = Mock(b=[Mock(a=i) for i in range(3)])

    # When
    data = BSerializer(obj).data

    # Then
    assert data == {"b": [{"a": 0}, {"a": 1}, {"a": 2},]}


def test_nested_serializers_with_call_option():
    # Having
    class ASerializer(Serializer):
        a = fields.Field()

    class BSerializer(Serializer):
        b = ASerializer(call=True)

    obj = Mock(**{"b.return_value.a": 3})

    # When
    data = BSerializer(obj).data

    # Then
    assert data == {"b": {"a": 3}}


def test_serializer_method_field():
    # Having
    class ASerializer(Serializer):
        a = fields.MethodField()
        b = fields.MethodField(method_name="add_9")

        def get_a(self, obj):
            return obj.a + 5

        def add_9(self, obj):
            return obj.a + 9

    obj = Mock(a=2)

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": 7, "b": 11}


def test_to_value_called():
    # Having
    class ASerializer(Serializer):
        a = fields.IntegerField()
        b = fields.FloatField(call=True)
        c = fields.CharField(attr_name="foo.bar.baz")

    obj = Mock(**{"a": 5, "b.return_value": "6.2", "foo.bar.baz": 10})

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": 5, "b": 6.2, "c": "10"}


def test_dict_serializer():
    # Having
    class ASerializer(DictSerializer):
        a = fields.IntegerField()
        b = fields.Field(attr_name="foo")

    d = {"a": "2", "foo": "hello"}

    # When
    data = ASerializer(d).data

    # Then
    assert data == {"a": 2, "b": "hello"}


def test_dotted_attribute_parameter():
    # Having
    class ASerializer(Serializer):
        a = fields.Field("a.b.c")

    obj = Mock(**{"a.b.c": 2})

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": 2}


def test_implementing_custom_field():
    # Having
    class Add5Field(fields.Field):
        def to_value(self, value):
            return value + 5

    class ASerializer(Serializer):
        a = Add5Field()

    obj = Mock(a=10)

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": 15}


def test_optional_integer_field_should_be_skipped_when_the_value_is_none():
    # Having
    class ASerializer(Serializer):
        a = fields.IntegerField(required=False)

    obj = Mock(a=None)

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": None}


def test_optional_integer_field_should_be_rendered_when_the_value_is_not_none():
    # Having
    class ASerializer(Serializer):
        a = fields.IntegerField(required=False)

    obj = Mock(a="5")

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": 5}


def test_required_integer_field_should_raise_serialization_error_if_none():
    # Having
    class ASerializer(Serializer):
        a = fields.IntegerField()

    obj = Mock(a=None)

    # Then
    with pytest.raises(SerializationError):
        # When
        ASerializer(obj).data


def test_optional_field_in_dictserializer_should_be_rendered_when_the_value_is_none():
    # Having
    class ASerializer(DictSerializer):
        a = fields.Field(required=False)

    # When
    data = ASerializer({"a": None}).data

    # Then
    assert data == {"a": None}


def test_optional_field_in_dictserializer_should_be_skipped_when_the_attribute_doesnt_exist():
    # Having
    class ASerializer(DictSerializer):
        a = fields.Field(required=False)

    # When
    data = ASerializer({}).data

    # Then
    assert data == {}


def test_required_field_in_dictserializer_should_raise_serialization_error_if_none():
    # Having
    class ASerializer(DictSerializer):
        a = fields.Field()

    # Then
    with pytest.raises(SerializationError):
        # When
        ASerializer({}).data


def test_optional_methodfield_should_return_value_even_if_the_returned_value_is_none():
    # Having
    class ASerializer(Serializer):
        a = fields.MethodField(required=False)

        def get_a(self, obj):
            return obj.a

    obj = Mock(a=None)

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": None}


def test_required_methodfield_should_return_value_even_if_the_returned_value_is_none():
    # Having
    class ASerializer(Serializer):
        a = fields.MethodField()

        def get_a(self, obj):
            return obj.a

    obj = Mock(a=None)

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": None}


def test_constant_field_with_none_value():
    # Having
    class ASerializer(Serializer):
        a = fields.ConstantField(constant=None)

    obj = Mock()

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": None}


def test_constant_field_with_primitive_constant():
    # Having
    class PISerializer(Serializer):
        pi = fields.ConstantField(constant=3.14)

    obj = Mock()

    # When
    data = PISerializer(obj).data

    # Then
    assert data == {"pi": 3.14}


def test_constant_field_with_list_of_primitive_constants():
    # Having
    class ASerializer(Serializer):
        http = fields.ConstantField(["GET", "POST", "PUT"])

    obj = Mock()

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"http": ["GET", "POST", "PUT"]}


def test_constant_field_with_nested_dict_of_primitive_constants():
    # Given
    class ASerializer(Serializer):
        users = fields.ConstantField(
            {
                "foo": {"id": 12, "totalReactions": 19},
                "bar": {"id": 33, "totalReactions": 122},
            },
            label="usersList",
        )

    obj = Mock()

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {
        "usersList": {
            "foo": {"id": 12, "totalReactions": 19},
            "bar": {"id": 33, "totalReactions": 122},
        }
    }


def test_required_constant_field_with_non_primitive_constant_should_raise_error():
    # Given
    user = Mock()  # Non-primitive type

    # Then
    with pytest.raises(SerializationError):
        # When
        class ASerializer(DictSerializer):
            users = fields.ConstantField({"foo": user}, label="usersList")


def test_optional_constant_field_with_non_primitive_constant_should_ignore_the_value():
    # Given
    user_1 = Mock()
    user_2 = Mock()

    class ASerializer(DictSerializer):
        users = fields.ConstantField(
            {"foo": user_1, "bar": user_2}, label="usersList", required=False
        )

    # When
    data = ASerializer({}).data

    # Then
    assert data == {}


def test_list_field_with_simple_integer_field():
    # Having
    class ASerializer(Serializer):
        a = fields.ListField(fields.IntegerField())

    obj = Mock(a=[1, 3, 8, 2])

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"a": [1, 3, 8, 2]}


def test_list_field_with_integer_field_having_custom_attributes():
    # Having
    class ASerializer(Serializer):
        a = fields.ListField(fields.IntegerField(attr_name="a.b", label="custom_list"))

    obj = Mock(**{"a.b": [1, 3, 8, 2]})

    # When
    data = ASerializer(obj).data

    # Then
    assert data == {"custom_list": [1, 3, 8, 2]}


def test_list_field_with_serializer_should_raise_error():
    # Having
    class ASerializer(Serializer):
        pass

    # When
    with pytest.raises(AssertionError) as exc_info:

        class BSerializer(Serializer):
            a = fields.ListField(ASerializer())

    # Then
    assert (
        str(exc_info.value)
        == "Cannot call `ListField()` with a Serializer object. An option `many=True` is available for serializers."
    )


def test_list_field_with_constant_field_should_raise_error():
    with pytest.raises(AssertionError) as exc_info:

        class ASerializer(Serializer):
            a = fields.ListField(fields.ConstantField(constant=3))

    # Then
    assert (
        str(exc_info.value)
        == "`ListField()` can only be called with primitive-types fields. Given field type: ConstantField"
    )


def test_list_field_with_method_field_should_raise_error():
    with pytest.raises(AssertionError) as exc_info:

        class ASerializer(Serializer):
            a = fields.ListField(fields.MethodField(method_name="custom_method"))

            def custom_method(self, obj):
                return obj.a

    # Then
    assert (
        str(exc_info.value)
        == "`ListField()` can only be called with primitive-types fields. Given field type: MethodField"
    )


def test_serializer_with_custom_output_label():
    # Having
    class ASerializer(Serializer):
        context = fields.CharField(label="@context")
        content = fields.MethodField(label="@content")

        def get_content(self, obj):
            return obj.content

    obj = Mock(context="http://foo/bar/baz/", content="http://baz/bar/foo/")

    # When
    data = ASerializer(obj).data

    # Then
    assert "context" not in data
    assert "content" not in data
    assert data["@context"] == "http://foo/bar/baz/"
    assert data["@content"] == "http://baz/bar/foo/"
