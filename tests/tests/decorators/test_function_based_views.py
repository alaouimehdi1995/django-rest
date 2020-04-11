# -*- coding: utf-8 -*-

import json
from mock import Mock

from django.http import JsonResponse

from django_rest.decorators import api_view
from django_rest.http.exceptions import (
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    PermissionDenied,
)
from django_rest.http.methods import HTTPMethods
from django_rest.permissions import IsAuthenticated, IsReadOnly


def test_api_view_should_conserve_decorated_function_informations():
    # Given
    def target_view(*args, **kwargs):
        """ This is a docstring example """
        return JsonResponse({})

    # When
    decorated_view = api_view()(target_view)

    # Then
    assert decorated_view.__name__ == "target_view"
    assert decorated_view.__doc__ == " This is a docstring example "
    assert decorated_view.__module__ == target_view.__module__


def test_api_view_decorator_should_grant_access_when_no_permission_class_is_specified():
    # Given
    target_function = Mock(return_value=JsonResponse({}, status=200))

    @api_view()
    def target_view(*args, **kwargs):
        return target_function(*args, **kwargs)

    request = Mock(user=None, method="POST")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = target_view(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 200
    target_function.assert_called_with(request, **target_view_kwargs)


def test_api_view_decorator_should_grant_access_when_permission_class_allows_access():
    # Given
    target_function = Mock(return_value=JsonResponse({}, status=200))

    @api_view(permission_class=IsReadOnly)
    def target_view(*args, **kwargs):
        return target_function(*args, **kwargs)

    request = Mock(method="GET")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = target_view(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 200
    target_function.assert_called_with(request, **target_view_kwargs)


def test_api_view_decorator_should_return_403_when_permission_class_forbids_access():
    # Given
    target_function = Mock(return_value=JsonResponse({}, status=200))

    @api_view(permission_class=IsReadOnly)
    def target_view(*args, **kwargs):
        return target_function(*args, **kwargs)

    request = Mock(method="POST")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = target_view(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 403
    assert json.loads(resp.content)["error_msg"] == PermissionDenied.RESPONSE_MESSAGE
    target_function.assert_not_called()


def test_api_view_decorator_should_return_405_method_not_allowed_when_using_forbidden_http_method():
    # Given
    target_function = Mock(return_value=JsonResponse({}, status=200))

    @api_view(
        permission_class=IsAuthenticated,
        allowed_methods=(HTTPMethods.GET, HTTPMethods.POST, HTTPMethods.PUT),
    )
    def target_view(*args, **kwargs):
        return target_function(*args, **kwargs)

    request = Mock(**{"method": "PATCH", "user.is_authenticated": True})
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = target_view(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 405
    assert json.loads(resp.content)["error_msg"] == MethodNotAllowed.RESPONSE_MESSAGE
    target_function.assert_not_called()


def test_api_view_decorator_should_return_correct_error_exception_when_view_raises_base_api_exception():
    # Given
    target_function = Mock(side_effect=NotFound())

    @api_view(permission_class=IsReadOnly)
    def target_view(*args, **kwargs):
        return target_function(*args, **kwargs)

    request = Mock(method="GET")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = target_view(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 404
    assert json.loads(resp.content)["error_msg"] == NotFound.RESPONSE_MESSAGE
    target_function.assert_called_with(request, **target_view_kwargs)


def test_api_view_decorator_should_return_500_internal_error_when_unkown_exception_is_raised_in_the_view():
    # Given
    target_function = Mock(side_effect=TypeError("NoneType has no attribute 'name'"))

    @api_view(permission_class=IsReadOnly)
    def target_view(*args, **kwargs):
        return target_function(*args, **kwargs)

    request = Mock(method="GET")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = target_view(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 500
    assert json.loads(resp.content)["error_msg"] == InternalServerError.RESPONSE_MESSAGE
    target_function.assert_called_with(request, **target_view_kwargs)
