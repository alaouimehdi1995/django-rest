# -*- coding: utf-8 -*-

from mock import Mock
import pytest

from django.test.client import RequestFactory
from django.views import View

from django_rest.decorators import api_view


rf = RequestFactory()


def _mock_view(**kwargs):
    kwargs.update({"__name__": "foo", "__module__": "bar", "__doc__": "baz"})
    return Mock(**kwargs)


def test_api_view_without_parenthesis_syntax_works_on_function_based_views(monkeypatch):
    # Given
    monkeypatch.setattr(
        "django_rest.decorators.inspect.isfunction", lambda x: isinstance(x, Mock)
    )
    request = rf.get("/whatever/?filter=true&page=3")
    target_view = _mock_view()
    target_kwargs = {"pk": 3, "foo": "bar"}

    decorated_view = api_view(target_view)

    # When
    decorated_view(request, **target_kwargs)

    # Then
    target_view.assert_called_once_with(
        request,
        url_params=target_kwargs,
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_api_view_with_parenthesis_without_args_syntax_works_on_function_based_views(
    monkeypatch,
):
    # Given
    monkeypatch.setattr(
        "django_rest.decorators.inspect.isfunction", lambda x: isinstance(x, Mock)
    )
    request = rf.get("/whatever/?filter=true&page=3")
    target_view = _mock_view()
    target_kwargs = {"pk": 3, "foo": "bar"}

    decorated_view = api_view()(target_view)

    # When
    decorated_view(request, **target_kwargs)

    # Then
    target_view.assert_called_once_with(
        request,
        url_params=target_kwargs,
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_api_view_with_parenthesis_with_args_syntax_works_on_function_based_views(
    monkeypatch,
):
    # Given
    monkeypatch.setattr(
        "django_rest.decorators.inspect.isfunction", lambda x: isinstance(x, Mock)
    )
    request = rf.get("/whatever/?filter=true&page=3")
    target_view = _mock_view()
    target_kwargs = {"pk": 3, "foo": "bar"}

    decorated_view = api_view(allowed_methods=("GET",))(target_view)

    # When
    decorated_view(request, **target_kwargs)

    # Then
    target_view.assert_called_once_with(
        request,
        url_params=target_kwargs,
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_api_view_without_parenthesis_syntax_works_on_class_based_views(monkeypatch):
    # Given
    monkeypatch.setattr(
        "django_rest.decorators.inspect.ismethod", lambda x: isinstance(x, Mock)
    )
    mocked_get = _mock_view()

    class CustomView(View):
        class_attribute = "foo"
        get = mocked_get

    request = rf.get("/whatever/?filter=true&page=3")
    target_kwargs = {"pk": 3, "foo": "bar"}

    DecoratedView = api_view(CustomView)

    # When
    DecoratedView().dispatch(request, **target_kwargs)

    # Then
    mocked_get.assert_called_once_with(
        request,
        url_params=target_kwargs,
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_api_view_with_parenthesis_without_args_syntax_works_on_class_based_views(
    monkeypatch,
):
    # Given
    monkeypatch.setattr(
        "django_rest.decorators.inspect.ismethod", lambda x: isinstance(x, Mock)
    )
    mocked_get = _mock_view()

    class CustomView(View):
        class_attribute = "foo"
        get = mocked_get

    request = rf.get("/whatever/?filter=true&page=3")
    target_kwargs = {"pk": 3, "foo": "bar"}

    DecoratedView = api_view()(CustomView)

    # When
    DecoratedView().dispatch(request, **target_kwargs)

    # Then
    mocked_get.assert_called_once_with(
        request,
        url_params=target_kwargs,
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_api_view_with_parenthesis_with_args_syntax_works_on_class_based_views(
    monkeypatch,
):
    # Given
    monkeypatch.setattr(
        "django_rest.decorators.inspect.ismethod", lambda x: isinstance(x, Mock)
    )
    mocked_get = _mock_view()

    class CustomView(View):
        class_attribute = "foo"
        get = mocked_get

    request = rf.get("/whatever/?filter=true&page=3")
    target_kwargs = {"pk": 3, "foo": "bar"}

    DecoratedView = api_view(allowed_methods=("GET",))(CustomView)

    # When
    DecoratedView().dispatch(request, **target_kwargs)

    # Then
    mocked_get.assert_called_once_with(
        request,
        url_params=target_kwargs,
        query_params={"filter": "true", "page": "3"},
        deserialized_data=None,
    )


def test_api_view_applied_to_a_invalid_class_raises_typeerror():
    # Given
    class InvalidView(object):
        pass

    # Then
    with pytest.raises(TypeError) as exc_info:
        # When
        api_view(InvalidView)

    assert str(exc_info.value) == (
        "The `@api_view` decorator is applied to either a function "
        "or a class inheriting from django.views.View. Given: InvalidView class"
    )


def test_api_view_applied_to_invalid_object_raises_typeerror():
    # Given
    invalid_variable = "foo bar"

    # Then
    with pytest.raises(TypeError) as exc_info:
        # When
        api_view(invalid_variable)

    assert str(exc_info.value) == (
        "The `@api_view` decorator is applied to either a function "
        "or a class inheriting from django.views.View. Given: str object"
    )
