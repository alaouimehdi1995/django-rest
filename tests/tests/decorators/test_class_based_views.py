# -*- coding: utf-8 -*-

import json
from mock import Mock

from django.http import JsonResponse
from django.views import View

from django_rest.decorators import api_view
from django_rest.http.exceptions import (
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    PermissionDenied,
)
from django_rest.http.methods import HTTPMethods
from django_rest.permissions import IsReadOnly, IsAuthenticated


def test_api_view_should_conserve_decorated_class_informations():
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
    DecoratedView = api_view()(CustomView)

    # Then
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


def test_api_view_decorator_should_grant_access_when_no_permission_is_specified():
    # Given
    get_target_function = Mock(return_value=JsonResponse({}, status=200))
    post_target_function = Mock(return_value=JsonResponse({}, status=201))

    @api_view()
    class TargetClassView(View):
        def get(self, request, *args, **kwargs):
            return get_target_function(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            return post_target_function(request, *args, **kwargs)

    request = Mock(user=None, method="POST")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = TargetClassView().dispatch(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 201
    post_target_function.assert_called_with(request, **target_view_kwargs)
    get_target_function.assert_not_called()


def test_api_view_decorator_should_grant_access_when_permission_grants_access():
    # Given
    get_target_function = Mock(return_value=JsonResponse({}, status=200))
    post_target_function = Mock(return_value=JsonResponse({}, status=201))

    @api_view(permission_class=IsReadOnly)
    class TargetClassView(View):
        def get(self, request, *args, **kwargs):
            return get_target_function(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            return post_target_function(request, *args, **kwargs)

    request = Mock(user=None, method="GET")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = TargetClassView().dispatch(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 200
    get_target_function.assert_called_with(request, **target_view_kwargs)
    post_target_function.assert_not_called()


def test_api_view_decorator_should_return_403_forbidden_response_when_user_is_not_allowed():
    # Given
    get_target_function = Mock(return_value=JsonResponse({}, status=200))
    post_target_function = Mock(return_value=JsonResponse({}, status=201))

    @api_view(permission_class=IsReadOnly)
    class TargetClassView(View):
        def get(self, request, *args, **kwargs):
            return get_target_function(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            return post_target_function(request, *args, **kwargs)

    request = Mock(user=None, method="POST")
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = TargetClassView().dispatch(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 403
    assert json.loads(resp.content)["error_msg"] == PermissionDenied.RESPONSE_MESSAGE
    post_target_function.assert_not_called()
    get_target_function.assert_not_called()


def test_api_view_decorator_should_return_405_method_not_allowed_when_using_forbidden_http_method():
    # Given
    post_target_function = Mock(return_value=JsonResponse({}, status=201))
    patch_target_function = Mock(return_value=JsonResponse({}, status=200))

    @api_view(
        permission_class=IsAuthenticated,
        allowed_methods=(HTTPMethods.GET, HTTPMethods.POST, HTTPMethods.PUT),
    )
    class TargetClassView(View):
        def post(self, request, *args, **kwargs):
            return post_target_function(request, *args, **kwargs)

        def patch(self, request, *args, **kwargs):
            return patch_target_function(request, *args, **kwargs)

    request = Mock(**{"method": "PATCH", "user.is_authenticated": True})
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = TargetClassView().dispatch(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 405
    assert json.loads(resp.content)["error_msg"] == MethodNotAllowed.RESPONSE_MESSAGE
    post_target_function.assert_not_called()
    patch_target_function.assert_not_called()


def test_api_view_decorator_should_return_correct_error_exception_when_view_raises_base_api_exception():
    # Given
    get_target_function = Mock(side_effect=NotFound())
    post_target_function = Mock(return_value=JsonResponse({}, status=201))

    @api_view(
        permission_class=IsReadOnly,
        allowed_methods=(HTTPMethods.GET, HTTPMethods.POST, HTTPMethods.PUT),
    )
    class TargetClassView(View):
        def get(self, request, *args, **kwargs):
            return get_target_function(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            return post_target_function(request, *args, **kwargs)

    request = Mock(**{"method": "GET", "user.is_authenticated": True})
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = TargetClassView().dispatch(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 404
    assert json.loads(resp.content)["error_msg"] == NotFound.RESPONSE_MESSAGE
    get_target_function.assert_called_with(request, **target_view_kwargs)
    post_target_function.assert_not_called()


def test_api_view_decorator_should_return_500_internal_error_when_unkown_exception_is_raised_in_the_view():
    # Given
    get_target_function = Mock(
        side_effect=TypeError("NoneType has no attribute 'name'")
    )
    post_target_function = Mock(return_value=JsonResponse({}, status=201))

    @api_view(
        permission_class=IsReadOnly,
        allowed_methods=(HTTPMethods.GET, HTTPMethods.POST, HTTPMethods.PUT),
    )
    class TargetClassView(View):
        def get(self, request, *args, **kwargs):
            return get_target_function(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            return post_target_function(request, *args, **kwargs)

    request = Mock(**{"method": "GET", "user.is_authenticated": True})
    target_view_kwargs = {"pk": 1, "all": False}

    # When
    resp = TargetClassView().dispatch(request, **target_view_kwargs)

    # Then
    assert resp.status_code == 500
    assert json.loads(resp.content)["error_msg"] == InternalServerError.RESPONSE_MESSAGE
    get_target_function.assert_called_with(request, **target_view_kwargs)
    post_target_function.assert_not_called()
