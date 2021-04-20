# -*- coding: utf-8 -*-

import six
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms.fields import Field
from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.utils import ErrorDict, ErrorList


class BaseDeserializer(Field):
    """
    The main implementation of Deserializers logic. Note that this class is
    slightly different from the classic Form.
    """

    __slots__ = ()

    empty_values = (None, "")

    def __init__(self, data=None, **kwargs):
        super(BaseDeserializer, self).__init__(**kwargs)
        self._init_data(data)

    def _init_data(self, data):
        # type:(Optional[Dict]) -> None
        self._data = data
        self._errors = None  # Stores the errors after `full_clean()` has been called.
        self._cleaned_data = None

    @classmethod
    def fields(cls):
        # type:() -> Iterator[str, Field]
        for name in cls.declared_fields:
            yield name, cls.declared_fields[name]

    @property
    def errors(self):
        # type:() -> ErrorDict
        """Return an ErrorDict for the data provided for the deserializer."""
        if self._errors is None:
            self.full_clean()
        return self._errors

    def is_valid(self):
        """Return True if the deserializer has no errors, or False otherwise."""
        return not self.errors

    def _get_error_dict(self, field_name, error):
        # type:(str, ValidationError) -> Dict
        if not hasattr(error, "error_dict"):
            # In case the error comes from simple ("flat") Field
            return {field_name or NON_FIELD_ERRORS: error.messages}

        # Nested field case (the Field itself is a Deserializer instance)
        return {field_name: dict(error)}

    def add_error(self, field_name, error):
        # type:(str, ValidationError) -> None
        """
        Updates the content of `self._errors`. Each `self._errors` is a `dict` instance.
        """
        error = self._get_error_dict(field_name, error)
        for field_name, errors in error.items():
            self._errors[field_name] = errors

    def full_clean(self):
        """
        Clean all of self._data and populate self._errors and self._cleaned_data.
        """
        self._errors = ErrorDict()
        self._cleaned_data = {}
        self._clean_fields()

    def _clean_fields(self):
        if self._data in self.empty_values:
            self._cleaned_data = self._data
            return
        if not isinstance(self._data, dict):
            error_list = ErrorList(["This field should be an object."])
            raise ValidationError(error_list)
        for name, field in self.declared_fields.items():
            value = self._data.get(name)
            try:
                value = field.clean(value)
                self._cleaned_data[name] = value
                if hasattr(self, "post_clean_{}".format(name)):
                    value = getattr(self, "post_clean_{}".format(name))(value)
                    self._cleaned_data[name] = value
            except ValidationError as e:
                if field.required:
                    self.add_error(name, e)

    def clean(self, data):
        """
        Overriden version of superclass Field.clean(). Called in case of nested
        Deserializers. Performs the validation and cleaning process on the data
        parameter. Returns the cleaned data to the parent deserializer.
        In case of error, Raises `ValidationError` with the whole ErrorDict()
        of its errors in order to be catched in the parent.
        """

        # Raises an error if `data` is empty and the current (nested)
        # deserializer is required.
        self.validate(data)

        self._init_data(data)
        if self.errors:
            raise ValidationError(self.errors)
        return self._cleaned_data

    @property
    def data(self):
        # type:() -> dict
        if not self._cleaned_data:
            self.full_clean()
        return self._cleaned_data


class Deserializer(six.with_metaclass(DeclarativeFieldsMetaclass, BaseDeserializer)):
    pass


class AllPassDeserializer(Deserializer):
    """Deserializer that accepts any given data. the clean always returns
    the data received as input.
    """

    def _clean_fields(self):
        for name, value in self._data.items():
            self._cleaned_data[name] = value
