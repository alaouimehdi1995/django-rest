# -*- coding: utf-8 -*-

import inspect
from functools import wraps


from django.http import JsonResponse
from django.views import View

from django_rest.http.exceptions import (
    BaseAPIException,
    InternalServerError,
    MethodNotAllowed,
    PermissionDenied,
)
from django_rest.http.methods import ALL_HTTP_METHODS
from django_rest.permissions import AllowAny


def _build_function_wrapper(permission_class, allowed_methods, view_function):
    @wraps(view_function)
    def function_wrapper(request, *args, **kwargs):
        # type:(HttpRequest, Any) -> JsonResponse
        try:
            if request.method not in allowed_methods:
                raise MethodNotAllowed
            if not permission_class().has_permission(request, view_function):
                raise PermissionDenied
            return view_function(request, *args, **kwargs)
        except BaseAPIException as e:
            return JsonResponse({"error_msg": e.RESPONSE_MESSAGE}, status=e.STATUS_CODE)
        except Exception:
            return JsonResponse(
                {"error_msg": InternalServerError.RESPONSE_MESSAGE},
                status=InternalServerError.STATUS_CODE,
            )

    return function_wrapper


def _build_class_wrapper(permission_class, allowed_methods, view_class):
    class ViewWrapper(object):
        __doc__ = view_class.__doc__
        __module__ = view_class.__module__

        def __init__(self, *args, **kwargs):
            self.wrapped_view = view_class(*args, **kwargs)

        def __getattribute__(self, name):
            try:
                return super(ViewWrapper, self).__getattribute__(name)
            except AttributeError:
                attribute = self.wrapped_view.__getattribute__(name)
                if not inspect.ismethod(attribute):
                    return attribute
                return _build_function_wrapper(
                    permission_class, allowed_methods, attribute
                )

    ViewWrapper.__name__ = view_class.__name__
    return ViewWrapper


def api_view(permission_class=AllowAny, allowed_methods=ALL_HTTP_METHODS):
    # type:(AbstractPermission, Tuple[str]) -> Callable
    def view_decorator(view):
        # type:(Callable) -> Callable
        if inspect.isfunction(view):
            return _build_function_wrapper(permission_class, allowed_methods, view)
        elif issubclass(view, View):
            return _build_class_wrapper(permission_class, allowed_methods, view)
        # TODO: here: raise error because the decorated object isn't a view

    return view_decorator
