# -*- coding: utf-8 -*-

import operator

import six

from django_rest.serializers.base import Field, SerializerBase
from django_rest.serializers.exceptions import SerializationError


def _compile_field_to_tuple(field, serializer_field_name, serializer_cls):
    getter = field.as_getter(serializer_field_name, serializer_cls)
    if getter is None:
        getter = serializer_cls.default_getter(field.attr_name or serializer_field_name)

    # Only set a to_value function if it has been overridden for performance.
    to_value = None
    if field._is_to_value_overridden():
        to_value = field.to_value

    # Set the field name to a supplied label; defaults to the attribute name.
    name = field.label or serializer_field_name

    return (
        name,
        getter,
        to_value,
        field.call,
        field.required,
        field.getter_needs_serializer_as_arg,
    )


class SerializerMeta(type):
    @staticmethod
    def _get_fields(direct_fields, serializer_cls):
        field_map = {}
        # Get all the fields from base classes.
        for cls in serializer_cls.__mro__[::-1]:
            if issubclass(cls, SerializerBase):
                field_map.update(cls._field_map)
        field_map.update(direct_fields)
        return field_map

    @staticmethod
    def _compile_fields(field_map, serializer_cls):
        return [
            _compile_field_to_tuple(field, name, serializer_cls)
            for name, field in field_map.items()
        ]

    def __new__(cls, name, bases, attrs):
        # Fields declared directly on the class.
        direct_fields = {}

        # Take all the Fields from the attributes.
        for attr_name, field in attrs.items():
            if isinstance(field, Field):
                direct_fields[attr_name] = field
        for k in direct_fields.keys():
            del attrs[k]

        real_cls = super(SerializerMeta, cls).__new__(cls, name, bases, attrs)

        field_map = cls._get_fields(direct_fields, real_cls)
        compiled_fields = cls._compile_fields(field_map, real_cls)

        real_cls._field_map = field_map
        real_cls._compiled_fields = tuple(compiled_fields)
        return real_cls


class Serializer(six.with_metaclass(SerializerMeta, SerializerBase)):
    """The Serializer class is used as a base for custom serializers.

    A Serializer class is also a subclass of Field class, which allows nesting
    Serializers. A new serializer is defined by subclassing the `Serializer` class,
    then adding each `Field` as a class variable.

    Example: :

        class FooSerializer(Serializer):
            foo = Field()
            bar = Field()

        foo = Foo(foo='hello', bar=5)
        serialized_obj = FooSerializer(foo).data
        # serialized_obj = {'foo': 'hello', 'bar': 5}

    :param instance: The object or iterable of objects to serialize.
    :param bool many: If `instance` is an iterable of objects, set `many` to `True`
        to serialize it as a list.
    """

    #: The default getter used if `Field.as_getter()` returns None.
    default_getter = operator.attrgetter

    def __init__(self, instance=None, many=False, **kwargs):
        super(Serializer, self).__init__(**kwargs)
        self.instance = instance
        self.many = many
        self._data = None

    def _serialize(self, instance, fields):
        # Transforms the `instance` object into its serialized value, by using
        # the `fields` list parameter.
        serialized_value = {}
        for name, getter, to_value, call, required, pass_self in fields:
            try:
                if pass_self:
                    result = getter(self, instance)
                else:
                    result = getter(instance)
                    if required or result is not None:
                        if call:
                            result = result()
                        if to_value:
                            result = to_value(result)
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                if required:
                    raise SerializationError(str(e))
            else:
                serialized_value[name] = result

        return serialized_value

    def to_value(self, instance):
        fields = self._compiled_fields
        if self.many:
            serialize = self._serialize
            return [serialize(o, fields) for o in instance]
        return self._serialize(instance, fields)

    @property
    def data(self):
        # type:() -> Dict[str, Any]
        """Get the serialized data from the Serializer instance. The data is cached
        for further accesses.
        """
        # Cache the data for next time `.data` is called.
        if self._data is None:
            self._data = self.to_value(self.instance)
        return self._data


class DictSerializer(Serializer):
    """DictSerializer serializes python `dicts` instead of objects.

    `DictSerializer` uses `operator.itemgetter` to fetch data from the object
    to serialize, while `Serializer` class uses `operator.attrgetter`.

    Example: ::

        class FooSerializer(DictSerializer):
            foo = IntField()
            bar = FloatField()

        foo = {'foo': '5', 'bar': '2.2'}
        serialized_obj = FooSerializer(foo).data
        # serialized_obj = {'foo': 5, 'bar': 2.2}
    """

    default_getter = operator.itemgetter
