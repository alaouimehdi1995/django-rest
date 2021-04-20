# -*- coding: utf-8 -*-

import types

import six

from django_rest.serializers.serializers import Serializer
from django_rest.serializers.base import Field
from django_rest.serializers.exceptions import SerializationError

if six.PY34:
    from collections.abc import Iterable, Mapping  # pragma: no cover
else:
    from collections import Iterable, Mapping  # pragma: no cover


NoneType = type(None)
UnicodeType = types.UnicodeType if six.PY2 else str


PRIMITIVE_TYPES = (
    bool,
    int,
    float,
    str,
    NoneType,
    UnicodeType,
)
ITERABLE_TYPES = (
    Iterable,
    Mapping,
)
ALLOWED_CONSTANT_TYPES = ITERABLE_TYPES + PRIMITIVE_TYPES


class CharField(Field):
    """ Field that converts the attribute's value into a string. """

    to_value = staticmethod(six.text_type)


class IntegerField(Field):
    """ Field that converts the attribute's value into an integer. """

    to_value = staticmethod(int)


class FloatField(Field):
    """ Field that converts the attribute's value into a float. """

    # TODO: implement precision

    to_value = staticmethod(float)


class BooleanField(Field):
    """ Field that converts the attribute's value into a boolean. """

    to_value = staticmethod(bool)


def _is_valid_field_instance(field_instance):
    # type:(Field) -> None
    assert not isinstance(
        field_instance, Serializer
    ), "Cannot call `ListField()` with a Serializer object. An option `many=True` is available for serializers."

    assert (
        field_instance._is_to_value_overridden()
    ), "`ListField()` can only be called with primitive-types fields. Given field type: {}".format(
        field_instance.__class__.__name__
    )


def ListField(field_instance):
    # type:(Field) -> Field
    """Allows to apply the Field.to_value() method on an iterable of values,
    instead of a single value. The same purpose could be achieved with `MethodField()`,
    but it'll be just too annoying.
    Example:

        class Subscription:
            status = ("active", "trialing", "canceled")

        class SubscriptionSerializer(Serializer):
            status = ListField(CharField(label="allowed_status", required=True))

        serialized_obj = SubscriptionSerializer(subscription).data
        # serialized_obj = {"allowed_status": ["active", "trialing", "canceled"]}

    :param field_instance: a Field instance that represents the type of a single element
        of the iterable to be passed to `to_value()` method.
        Note that the `field_instance` cannot be a `MethodField()`, a `ConstantField()`
        or a `Serializer` (which has the option `many=True` for the same purpose).
    The `ListField` generates a new field class (and instance) during the declaration
    (before the runtime), for perfomance purpose.
    """
    _is_valid_field_instance(field_instance)
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
    A Field that allows to constant data injection into the serialized object, without
    the need to declare an (serialized) object method, or a serializer's `MethodField()`
    to return a constant.
    For example:

        foo_const = "Foo"
        class FooSerializer(Serializer):
            foo = ConstantField(label="foo_constant", required=False, constant=foo_const)
            bar = IntegerField()
        foo = Foo(bar=5)
        serialized_foo = FooSerializer(foo).data
        # serialized_foo = {'foo': "Foo", 'bar': 5}


    :param str label: Same as other fields.
    :param bool required: Same as other fields.
    :param constant: The constant to be added in the serialized object. Should be
        a combination (`list`, `dict` or single value) of primitive type (int, float,
        str, bool, None).
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
        # type:(str, Serializer) -> Callable
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
        # type:(Any) -> bool
        if not isinstance(constant, ALLOWED_CONSTANT_TYPES):
            return False

        if isinstance(constant, PRIMITIVE_TYPES):
            return True

        if isinstance(constant, Mapping):
            keys_are_primitive = all(
                isinstance(key, (str, UnicodeType)) for key in constant.keys()
            )
            return keys_are_primitive and all(
                cls._is_primitive_const(value) for value in constant.values()
            )

        # The case of iterable
        return all(cls._is_primitive_const(element) for element in constant)


class MethodField(Field):
    """A Field class that calls a method on the `Serializer` class.

    This is useful if a Field needs to serialize a value that may come from multiple
    attributes on the same object. For example:

        class FooSerializer(Serializer):
            plus = MethodField()
            minus = MethodField('do_minus')

            def get_plus(self, foo_obj):
                return foo_obj.bar + foo_obj.baz

            def do_minus(self, foo_obj):
                return foo_obj.bar - foo_obj.baz

        foo = Foo(bar=5, baz=10)
        serialized_obj = FooSerializer(foo).data
        # serialized_obj = {'plus': 15, 'minus': -5}

    :param str method_name: The serializer's method name to be called. Defaults to
        `get_<field name>`.
    """

    __slots__ = ("label", "required", "method_name")
    getter_needs_serializer_as_arg = True

    def __init__(self, method_name=None, **kwargs):
        super(MethodField, self).__init__(**kwargs)
        self.method_name = method_name

    def as_getter(self, serializer_field_name, serializer_cls):
        # type:(str, Serializer) -> Callable
        method_name = self.method_name
        if method_name is None:
            method_name = "get_{0}".format(serializer_field_name)
        return getattr(serializer_cls, method_name)
