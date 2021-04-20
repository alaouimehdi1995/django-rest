# -*- coding: utf-8 -*-

import types


class Field(object):
    """The Field class is used to define what attributes will be serialized.

    It maps a property or function on an object to a value in the serialized result.
    Subclass this to make custom fields. For most simple cases, overriding
    Field.to_value() should be enough. For more control, you may override
    Field.as_getter().

    :param str attr_name: The attribute to get on the object. If not supplied,
        the name the current field was assigned to inside the serializer will be used.
    :param bool call: Whether the value should be called after it is retrieved
        from the object. Useful if an object has a method to be serialized.
    :param str label: A label to use as the name of the serialized field
        instead of using the attribute name of the field.
    :param bool required: Whether the field is required. If set to `False`,
        the method Field.to_value() will not be called if the value is `None` or
        an error is raised during its serialization.
    """

    __slots__ = ("attr_name", "call", "label", "required")

    #  Set to `True` if the value function returned from the method Field.as_getter()
    #  requires the serializer to be passed in as the first argument. Otherwise,
    #  the object will be the only parameter.
    getter_needs_serializer_as_arg = False

    def __init__(self, attr_name=None, call=False, label=None, required=True):
        self.attr_name = attr_name
        self.call = call
        self.label = label
        self.required = required

    def to_value(self, value):
        # type:(Any) -> Any
        """Transforms the serialized value. It could be used for cleaning
        and validating the value serialized by the current field. For example,
        to implement an `int` field, the Field.to_value() method will looks like:

            def to_value(self, value):
                return int(value)

        :param value: The value fetched from the object being serialized.
        """
        return value

    to_value._base_implementation = True

    def _is_to_value_overridden(self):
        # type:() -> bool
        to_value = self.to_value
        # If to_value isn't a method, it must have been overridden.
        if not isinstance(to_value, types.MethodType):
            return True
        return not getattr(to_value, "_base_implementation", False)

    def as_getter(self, serializer_field_name, serializer_cls):
        # type:(str, type) -> Optional[Callable]
        """Returns a function that fetches an attribute from an object.

        If `None` is returned, the default getter defined in `Serializer.default_getter`
        will be used instead.

        When a `Serializer` class is defined, each `Field` class will be
        compiled into a getter function using `æs_geter()` method. During the serialization
        process, each getter will be called with the object being serialized, then,
        the value returned from the getter will be passed through Field.to_value()
        method.

        If a `Field` class has set the `getter_needs_serializer_as_arg` to `True`,
        then the getter returned from the current method will be called with the
        `Serializer` instance as the first argument, and the object being serialized
        as the second.

        :param str serializer_field_name: The name this field was assigned to on the
            serializer.
        :param serializer_cls: The :class:`Serializer` this field is defined in.
        """
        return None


class SerializerBase(Field):
    _field_map = {}
