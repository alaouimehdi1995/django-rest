# -*- coding: utf-8 -*-

import inspect
import json
import pytest
from mock import Mock


from django.http import QueryDict
from django.test.client import RequestFactory
from django.views import View

from django_rest.decorators.utils import (
    build_class_wrapper,
    build_deserializer_map,
    build_function_wrapper,
    extract_request_payload,
    transform_query_dict_into_regular_dict,
)
from django_rest.deserializers import Deserializer, AllPassDeserializer
from django_rest.http.exceptions import (
    BaseAPIException,
    InternalServerError,
    PermissionDenied,
)
from django_rest.permissions import AllowAny, BasePermission


rf = RequestFactory()


def _mock_view(**kwargs):
    kwargs.update({"__name__": "foo", "__module__": "bar", "__doc__": "baz"})
    return Mock(**kwargs)


class AllowNone(BasePermission):
    def has_permission(self, request, view):
        return False


def test_transform_querydict_into_regular_dict():
    # Given
    query_dict = QueryDict("foo=3&foo=4&foo=5&bar=1&baz=true&collapse")

    # When
    _dict = transform_query_dict_into_regular_dict(query_dict)

    # Then
    assert _dict == {
        "foo": ["3", "4", "5"],
        "bar": "1",
        "baz": "true",
        "collapse": "",
    }


def test_deserializer_map_with_custom_deserializer_class():
    # Given
    class CustomDeserializer(Deserializer):
        pass

    # When
    deserializer_map = build_deserializer_map(CustomDeserializer)

    # Then
    assert deserializer_map == {
        "POST": CustomDeserializer,
        "PUT": CustomDeserializer,
        "PATCH": CustomDeserializer,
    }


def test_deserializer_map_with_complete_dict():
    # Given
    class CustomDeserializer(Deserializer):
        pass

    deserializer_init_map = {
        "POST": CustomDeserializer,
        "PUT": CustomDeserializer,
        "PATCH": CustomDeserializer,
    }

    # When
    deserializer_map = build_deserializer_map(CustomDeserializer)

    # Then
    assert deserializer_map == deserializer_init_map


def test_deserializer_map_with_incomplete_dict():
    # Given
    class CustomDeserializer(Deserializer):
        pass

    deserializer_init_map = {
        "POST": CustomDeserializer,
    }

    # When
    deserializer_map = build_deserializer_map(deserializer_init_map)

    # Then
    assert deserializer_map == {
        "POST": CustomDeserializer,
        "PUT": AllPassDeserializer,
        "PATCH": AllPassDeserializer,
    }


def test_deserializer_map_with_invalid_type_deserializer():
    # Given
    class InvalidDeserializer(object):
        pass

    # Then
    with pytest.raises(TypeError):
        # When
        build_deserializer_map(InvalidDeserializer)


def test_deserializer_map_with_dict_having_invalid_value():
    # Given
    class InvalidDeserializer(object):
        pass

    deserializer_init_map = {
        "POST": AllPassDeserializer,
        "PUT": InvalidDeserializer,
    }

    # Then
    with pytest.raises(TypeError):
        # When
        build_deserializer_map(deserializer_init_map)


def test_extract_payload_from_get_method_without_payload():
    assert extract_request_payload(rf.get("/whatever/")) is None


def test_extract_payload_from_get_method_with_payload():
    # Given
    payload = {"foo": "bar", "baz": 3}
    request = rf.get("/whatever/", payload)
    # Then
    # None because the content is saved as queryparams for GET method
    assert extract_request_payload(request, True) is None
    assert extract_request_payload(request, False) is None


def test_extract_payload_from_post_method_application_json():
    # Given
    payload = {"foo": "bar", "baz": 3}
    json_payload = json.dumps(payload)
    request = rf.post("/whatever/", data=json_payload, content_type="application/json")
    # Then
    assert extract_request_payload(request, False) == payload
    assert extract_request_payload(request, True) == payload


def test_extract_payload_from_post_method_form():
    # Given
    payload = {"foo": "bar", "baz": 3}
    request = rf.post("/whatever/", payload)
    # Then
    assert extract_request_payload(request, True) == {
        "foo": "bar",
        "baz": "3",
    }
    with pytest.raises(PermissionDenied):
        extract_request_payload(request, allow_form_data=False)


def test_extract_payload_put_method():
    # Given
    payload = {"foo": "bar", "baz": 3}
    json_payload = json.dumps(payload)
    request = rf.put("/whatever/", data=json_payload, content_type="application/json")
    # Then
    assert extract_request_payload(request, False) == payload
    assert extract_request_payload(request, True) == payload


def test_extract_payload_delete_method():
    assert extract_request_payload(rf.delete("/whatever/")) is None


def test_function_wrapper_conserves_view_informations():
    # Given
    def target_view(*args, **kwargs):
        """ This is a docstring example """

    # When
    decorated_view = build_function_wrapper(Mock(), Mock(), Mock(), Mock(), target_view)

    # Then
    assert inspect.isfunction(decorated_view)
    assert decorated_view.__name__ == "target_view"
    assert decorated_view.__doc__ == " This is a docstring example "
    assert decorated_view.__module__ == target_view.__module__


def test_function_wrapper_returns_403_when_permission_class_returns_false():
    # Given
    request = rf.get("/whatever/")
    target_view = _mock_view()

    # When
    decorated_view = build_function_wrapper(
        AllowNone, ("GET",), Mock(), Mock(), target_view
    )
    resp = decorated_view(request)

    # Then
    assert resp.status_code == 403
    target_view.assert_not_called()


def test_function_wrapper_returns_405_when_method_not_allowed():
    # Given
    request = rf.get("/whatever/")
    target_view = _mock_view()

    # When
    decorated_view = build_function_wrapper(
        AllowAny, ("POST",), Mock(), Mock(), target_view
    )
    resp = decorated_view(request)

    # Then
    assert resp.status_code == 405
    target_view.assert_not_called()


def test_function_wrapper_returns_400_when_data_isnt_valid():
    # Given
    payload = {"foo": "bar", "baz": 3}
    json_payload = json.dumps(payload)
    request = rf.post("/whatever/", data=json_payload, content_type="application/json")
    target_view = _mock_view()
    allow_forms = False

    class PreventDeserializer(Deserializer):
        def is_valid(self):
            return False

    deserializer_map = {"POST": PreventDeserializer}

    # When
    decorated_view = build_function_wrapper(
        AllowAny, ("POST",), deserializer_map, allow_forms, target_view
    )
    resp = decorated_view(request)

    # Then
    assert resp.status_code == 400
    target_view.assert_not_called()


def test_function_wrapper_calls_the_target_view_when_the_post_request_is_correct():
    # Given
    payload = {"foo": "bar", "baz": 3}
    json_payload = json.dumps(payload)
    request = rf.post(
        "/whatever/?filter=true&page=3",
        data=json_payload,
        content_type="application/json",
    )
    target_view = _mock_view()
    deserializer_map = {"POST": AllPassDeserializer}
    allow_forms = False

    # When
    decorated_view = build_function_wrapper(
        AllowAny, ("POST",), deserializer_map, allow_forms, target_view
    )
    decorated_view(request, pk=3, foo="bar")

    # Then
    target_view.assert_called_once_with(
        request,
        url_params={"pk": 3, "foo": "bar"},
        query_params={"filter": "true", "page": "3"},
        deserialized_data=payload,
    )


def test_function_wrapper_calls_the_target_view_when_the_get_request_is_correct():
    # Given
    request = rf.get("/whatever/", data={"filter": "true", "page": "3"})
    target_view = _mock_view()
    decorated_view = build_function_wrapper(AllowAny, ("GET",), {}, False, target_view)

    # When
    decorated_view(request, pk=3, foo="bar")

    # Then
    target_view.assert_called_once_with(
        request,
        url_params={"pk": 3, "foo": "bar"},
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_function_wrapper_should_return_correct_status_code_when_base_api_exception_is_raised():
    # Given
    class CustomApiException(BaseAPIException):
        STATUS_CODE = 489
        RESPONSE_MESSAGE = "Foo bar exception"

    request = rf.get("/whatever/")
    target_view = _mock_view(side_effect=CustomApiException())

    # When
    decorated_view = build_function_wrapper(AllowAny, ("GET",), {}, False, target_view)
    resp = decorated_view(request)

    # Then
    target_view.assert_called_once_with(
        request, url_params={}, query_params={}, deserialized_data=None
    )
    assert resp.status_code == 489
    assert json.loads(resp.content.decode())["error_msg"] == "Foo bar exception"


def test_function_wrapper_should_return_500_when_unkown_exception_is_raised_in_the_view():
    # Given
    target_view = _mock_view(side_effect=TypeError("NoneType has no attribute 'name'"))
    request = RequestFactory().get("/whatever/")

    # When
    decorated_view = build_function_wrapper(AllowAny, ("GET",), {}, False, target_view)
    resp = decorated_view(request)

    # Then
    assert resp.status_code == 500
    assert (
        json.loads(resp.content.decode())["error_msg"]
        == InternalServerError.RESPONSE_MESSAGE
    )
    target_view.assert_called_once_with(
        request, url_params={}, query_params={}, deserialized_data=None
    )


def test_class_wrapper_conserves_class_view_informations():
    # Given
    class CustomView(View):
        """ Custom view for custom purpose """

        def get(self, request, pk):
            """ Returns the last data """
            return

        def post(self, request, **kwargs):
            """ Creates object in DB from the received kwargs """
            pass

    # When
    DecoratedView = build_class_wrapper(Mock(), Mock(), Mock(), Mock(), CustomView)

    # Then
    assert inspect.isclass(DecoratedView)
    assert issubclass(DecoratedView, View)
    assert DecoratedView.__name__ == "CustomView"
    assert DecoratedView.__doc__ == " Custom view for custom purpose "
    assert DecoratedView.__module__ == CustomView.__module__

    assert DecoratedView().get.__name__ == "get"
    assert DecoratedView().post.__name__ == "post"

    assert DecoratedView().get.__doc__ == " Returns the last data "
    assert (
        DecoratedView().post.__doc__
        == " Creates object in DB from the received kwargs "
    )


def test_class_wrapper_conserves_all_methods_and_attributes_of_wrapped_view():
    # Given
    class CustomView(View):
        class_attribute = "foo"

        def __init__(self, *args, **kwargs):
            self.instance_attribute = "bar"

        def get(self, request, pk):
            return

        def _protected_method(self):
            pass

    # When
    DecoratedView = build_class_wrapper(Mock(), Mock(), Mock(), Mock(), CustomView)

    # Then
    assert DecoratedView().class_attribute == "foo"
    assert DecoratedView().instance_attribute == "bar"
    assert hasattr(DecoratedView(), "_protected_method")
    assert hasattr(DecoratedView(), "get")


def test_class_wrapper_decorates_http_methods_only():
    # Given
    class CustomView(View):
        class_attr = 2000

        def __init__(self):
            self.instance_attr = 3000

        def dispatch(self, request, *args, **kwargs):
            pass

        def get(self, request, pk):
            return

        def public_method(self, arg1, arg2):
            return arg1 + arg2

        def _protected_method(self):
            return 3

    # When
    DecoratedView = build_class_wrapper(Mock(), Mock(), Mock(), Mock(), CustomView)
    decorated_view = DecoratedView()
    original_view = decorated_view._wrapped_view

    # Then
    assert decorated_view.class_attr == original_view.class_attr
    assert decorated_view.instance_attr == original_view.instance_attr
    assert decorated_view.public_method == original_view.public_method
    assert decorated_view._protected_method == original_view._protected_method
    assert decorated_view.get != original_view.get
    assert decorated_view.dispatch != original_view.dispatch  # redefined in the wrapper
