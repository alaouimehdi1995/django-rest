# -*- coding: utf-8 -*-

from collections import Iterable, Mapping
import six
import types

from django_rest.serializers import Serializer
from django_rest.serializers.base import Field
from django_rest.serializers.exceptions import SerializationError

PRIMITIVE_TYPES = (
    types.BooleanType,
    types.IntType,
    types.FloatType,
    types.NoneType,
    types.StringType,
    types.UnicodeType,
)
ITERABLE_TYPES = (
    Iterable,
    Mapping,
)
ALLOWED_CONSTANT_TYPES = ITERABLE_TYPES + PRIMITIVE_TYPES


class CharField(Field):
    """A :class:`Field` that converts the value to a string."""

    to_value = staticmethod(six.text_type)


class IntegerField(Field):
    """A :class:`Field` that converts the value to an integer."""

    to_value = staticmethod(int)


class FloatField(Field):
    """A :class:`Field` that converts the value to a float."""

    # TODO: implement precision

    to_value = staticmethod(float)


class BooleanField(Field):
    """A :class:`Field` that converts the value to a boolean."""

    to_value = staticmethod(bool)


def _check_field_type_for_list_field(field_instance):
    assert not isinstance(
        field_instance, Serializer
    ), "Cannot call `ListField()` with a Serializer object. An option `many=True` is available for serializers."

    assert (
        field_instance._is_to_value_overridden()
    ), "`ListField()` can only be called with primitive-types fields. Given field type: {}".format(
        field_instance.__class__.__name__
    )


def ListField(field_instance):
    """
    A :function: that allows the serialization of an iterable of values having the same type.
    Could be done with a `MethodField` as well, but it would be too annoying.
    Example:
    class Subscription:
        status = ("active", "trialing", "canceled")  # Works with instance attributes as well

    class SubscriptionSerializer(Serializer):
        status = ListField(CharField(label="allowed_status", required=True))
        # Probably other fields here

    SubscriptionSerializer(subscription).data
    # {"allowed_status": ["active", "trialing", "canceled"]}

    :param field: a `Field` instance that represents the type of a single element
        the attribute to serialize. The `Field` cannot be a `Serializer` (for that,
        you have the option `many=True`), or a`MethodField`, or even a `ConstantField`
    """
    _check_field_type_for_list_field(field_instance)
    field_class = field_instance.__class__
    ListFieldClass = type(
        "List{}".format(field_class.__name__),
        (field_class,),
        {"__doc__": field_class.__doc__},
    )
    attrs = {name: getattr(field_instance, name) for name in field_instance.__slots__}

    def to_value(value):
        return [field_instance.to_value(v) for v in value]

    ListFieldClass.to_value = staticmethod(to_value)
    return ListFieldClass(**attrs)


class ConstantField(Field):
    """
    A :class:`Field` that allows to inject constant data into the serialized object,
    without having to touch the original object, or use `MethodField` to return a constant.
    For example:

        foo_const = "Foo"
        class FooSerializer(Serializer):
            foo = ConstantField(label="foo_constant", required=False, constant=foo_const)
            bar = IntegerField()
        foo = Foo(bar=5)
        FooSerializer(foo).data
        # {'foo': "Foo", 'bar': 5}


    :param constant: The constant to add in the serialized object. Should be primitive
        (int, float, str, bool, None), list of primitives, or a dict (even nested) of primitives.
    """

    __slots__ = ("label", "required", "constant", "_is_primitive")

    def __init__(self, constant=None, label=None, required=True):
        self.label = label
        self.required = required
        self.attr_name = None
        self.call = False
        self._is_primitive = self._is_primitive_const(constant)

        if not self._is_primitive and self.required:
            raise SerializationError(
                "Only primitive types are accepted in `ConstantField` (int, float, str, "
                "bool, None, unicode) and iterables/dict of primitive types. "
                "type({}) = {}.".format(constant, constant.__class__.__name__)
            )
        self.constant = constant

    def as_getter(self, serializer_field_name, serializer_cls):
        constant = self.constant

        def getter(obj):
            if not self._is_primitive and not self.required:
                # This raise will make the `_serialize` method `continue` the
                # loop without saving the current field
                raise TypeError(
                    "Non-required field: Non primitive constant given: {}".format(
                        constant.__class__.__name__
                    )
                )
            return constant

        return getter

    @classmethod
    def _is_primitive_const(cls, constant):
        if not isinstance(constant, ALLOWED_CONSTANT_TYPES):
            return False

        if isinstance(constant, PRIMITIVE_TYPES):
            return True

        if isinstance(constant, Mapping):
            keys_are_primitive = all(
                isinstance(key, (types.StringType, types.UnicodeType))
                for key in constant.keys()
            )
            return keys_are_primitive and all(
                cls._is_primitive_const(value) for value in constant.values()
            )

        # The case of iterable
        return all(cls._is_primitive_const(element) for element in constant)


class MethodField(Field):
    """A :class:`Field` that calls a method on the :class:`Serializer`.

    This is useful if a :class:`Field` needs to serialize a value that may come
    from multiple attributes on an object. For example: ::

        class FooSerializer(Serializer):
            plus = MethodField()
            minus = MethodField('do_minus')

            def get_plus(self, foo_obj):
                return foo_obj.bar + foo_obj.baz

            def do_minus(self, foo_obj):
                return foo_obj.bar - foo_obj.baz

        foo = Foo(bar=5, baz=10)
        FooSerializer(foo).data
        # {'plus': 15, 'minus': -5}

    :param str method_name: The method on the serializer to call. Defaults to
        ``'get_<field name>'``.
    """

    __slots__ = ("label", "required", "method_name")
    getter_takes_serializer = True

    def __init__(self, method_name=None, **kwargs):
        super(MethodField, self).__init__(**kwargs)
        self.method_name = method_name

    def as_getter(self, serializer_field_name, serializer_cls):
        method_name = self.method_name
        if method_name is None:
            method_name = "get_{0}".format(serializer_field_name)
        return getattr(serializer_cls, method_name)
