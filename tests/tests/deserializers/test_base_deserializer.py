# -*- coding: utf-8 -*-

from django_rest.deserializers import AllPassDeserializer, Deserializer, fields


def test_fields_method_should_iterate_over_form_fields():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=True, min_value=0)
        bar = fields.FloatField(required=False)

    # When
    deserializer_fields = list(SimpleDeserializer.fields())

    # Then
    assert deserializer_fields == [
        ("foo", SimpleDeserializer.declared_fields["foo"]),
        ("bar", SimpleDeserializer.declared_fields["bar"]),
    ]


def test_post_clean_method_within_deserializer_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=True, min_value=0)
        bar = fields.FloatField(required=False)

        def post_clean_bar(self, value):
            return value * 2

    payload = {"foo": "3", "bar": "3.44"}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": 3, "bar": 6.88}


def test_simple_deserializer_non_required_valid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=True, min_value=0)
        bar = fields.FloatField(required=False)

    payload = {"foo": "3", "bar": "3.44"}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": 3, "bar": 3.44}


def test_simple_deserializer_non_required_invalid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=True, min_value=0)
        bar = fields.FloatField(required=False)

    payload = {"foo": "3", "bar": "invalid value"}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": 3}


def test_simple_deserializer_non_required_non_existent_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=False, min_value=0)
        bar = fields.CharField(required=False, max_length=50)

    payload = {}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": None, "bar": ""}  # empty value for char is ''


def test_simple_deserializer_required_valid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=True, min_value=0)
        bar = fields.CharField(required=True, max_length=50)

    payload = {"foo": "3", "bar": "test value"}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": 3, "bar": "test value"}


def test_simple_deserializer_required_invalid_data_should_fail():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=True, min_value=0)
        bar = fields.FloatField(required=True)

    payload = {"foo": "3", "bar": "invalid value"}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert not deserializer.is_valid()
    assert deserializer.errors == {"bar": ["Enter a number."]}


def test_simple_deserializer_required_non_existent_data_should_fail():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.IntegerField(required=False, min_value=0)
        bar = fields.CharField(required=True, max_length=50)

    payload = {}

    # When
    deserializer = SimpleDeserializer(payload)

    # Then
    assert not deserializer.is_valid()
    assert deserializer.errors == {"bar": ["This field is required."]}


def test_nested_deserializer_required_valid_nested_required_valid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": {"foo": "48.43"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {"foo": 48.43}}


def test_nested_deserializer_required_invalid_data_should_fail():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": 3}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert not deserializer.is_valid()
    assert deserializer.errors == {"bar": ["This field should be an object."]}


def test_nested_deserializer_required_non_existent_data_should_fail():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3"}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert not deserializer.is_valid()
    assert deserializer.errors == {"bar": ["This field is required."]}


def test_nested_deserializer_required_valid_nested_non_required_valid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=False)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": {"foo": "3.14"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {"foo": 3.14}}


def test_nested_deserializer_required_valid_nested_non_required_invalid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=False)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": {"foo": "invalid value"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {}}


def test_nested_deserializer_required_valid_nested_non_required_non_existent_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=False)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": {}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {"foo": None}}


def test_nested_deserializer_required_valid_nested_required_invalid_data_should_fail():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": {"foo": "invalid value"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert not deserializer.is_valid()
    assert deserializer.errors == {"bar": {"foo": ["Enter a number."]}}


def test_nested_deserializer_required_valid_nested_required_non_existent_data_should_fail():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=True)

    payload = {"pk": "3", "bar": {}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert not deserializer.is_valid()
    assert deserializer.errors == {"bar": {"foo": ["This field is required."]}}


def test_nested_deserializer_non_required_invalid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3", "bar": 3}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3}


def test_nested_deserializer_non_required_non_existent_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3"}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": None}


def test_nested_deserializer_non_required_valid_nested_required_invalid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3", "bar": {"foo": "invalid value"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3}


def test_nested_deserializer_non_required_valid_nested_required_non_existent_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=True)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3", "bar": {}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3}


def test_nested_deserializer_non_required_valid_nested_non_required_valid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=False)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3", "bar": {"foo": "134.2"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {"foo": 134.2}}


def test_nested_deserializer_non_required_valid_nested_non_required_invalid_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=False)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3", "bar": {"foo": "invalid data"}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {}}


def test_nested_deserializer_non_required_valid_nested_non_required_non_existent_data_should_succeed():
    # Given
    class SimpleDeserializer(Deserializer):
        foo = fields.FloatField(required=False)

    class NestedDeserializer(Deserializer):
        pk = fields.IntegerField(required=True)
        bar = SimpleDeserializer(required=False)

    payload = {"pk": "3", "bar": {}}

    # When
    deserializer = NestedDeserializer(payload)

    # Then
    assert deserializer.is_valid()
    assert deserializer.data == {"pk": 3, "bar": {"foo": None}}


def test_validate_any_deserializer_should_validate_any_kind_of_data():
    deserializer = AllPassDeserializer(data={})
    assert deserializer.is_valid()
    assert deserializer.data == {}

    deserializer = AllPassDeserializer(data={"foo": "bar"})
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": "bar"}

    deserializer = AllPassDeserializer(data={"foo": {"bar": "baz", "baz": 3}})
    assert deserializer.is_valid()
    assert deserializer.data == {"foo": {"bar": "baz", "baz": 3}}
