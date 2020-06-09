# -*- coding: utf-8 -*-

import inspect
import json
from functools import wraps


from django.http import JsonResponse
from django.views import View

from django_rest.deserializers import (
    Deserializer,
    AllPassDeserializer,
)
from django_rest.http.exceptions import (
    BadRequest,
    BaseAPIException,
    InternalServerError,
    MethodNotAllowed,
    PermissionDenied,
)
from django_rest.http.methods import ALL_HTTP_METHODS, HTTP_METHODS_SUPPORTING_PAYLOAD
from django_rest.permissions import BasePermission

FORMS_CONTENT_TYPES = (
    "application/x-www-form-urlencoded",
    "multipart/form-data",
)


def build_deserializer_map(deserializer_class):
    if isinstance(deserializer_class, dict):
        if not all(
            issubclass(elem, Deserializer) for elem in deserializer_class.values()
        ):
            raise TypeError(
                "The values of the `deserializer_class` mapping "
                "should be subclass of `Deserializer`."
            )
        return {
            http_method: deserializer_class.get(http_method, AllPassDeserializer)
            for http_method in HTTP_METHODS_SUPPORTING_PAYLOAD
        }
    if issubclass(deserializer_class, Deserializer):
        return {
            http_method: deserializer_class
            for http_method in HTTP_METHODS_SUPPORTING_PAYLOAD
        }

    raise TypeError(
        "`deserializer_class` parameter should be either a subclass of `Deserializer` "
        "or a dict of `Deserializer` classes, not {}".format(
            deserializer_class.__name__
        )
    )


def transform_query_dict_into_regular_dict(query_dict):
    return {
        key: list_val if len(list_val) > 1 else list_val[0]
        for key, list_val in dict(query_dict).items()
    }


def extract_request_payload(request, allow_form_data=False):
    """
    Return the request's content (form or data).
    For `POST`, `PUT` and `PATCH` requests:
    - If the form data is allowed and the request is a form, returns a `dict`
    - If the form data isn't allowed and the request is a form, raises
      PermissionDenied exception.
    - For application/json requests, returns a `dict` containing the request's
      data
    For other HTTP methods:
    - Returns `None`
    """
    method = request.method
    if not allow_form_data and request.content_type in FORMS_CONTENT_TYPES:
        raise PermissionDenied  # OR bad request ?
    elif request.content_type in FORMS_CONTENT_TYPES and request.method == "POST":
        return transform_query_dict_into_regular_dict(request.POST)

    if method not in HTTP_METHODS_SUPPORTING_PAYLOAD:
        return None

    return json.loads(request.body.decode())


def build_function_wrapper(
    permission_class,  # type: BasePermission
    allowed_methods,  # type: Iterable[str]
    deserializers_http_methods_map,  # type: Dict[str, ClassVar[Deserializer]]
    allow_forms,  # type: bool
    view_function,  # Callable
):  # type:(...) -> Callable
    @wraps(view_function)
    def function_wrapper(request, *args, **kwargs):
        # type:(HttpRequest, List[Any]) -> JsonResponse
        try:
            if request.method not in allowed_methods:
                raise MethodNotAllowed
            if not permission_class().has_permission(request, view_function):
                raise PermissionDenied
            query_params = transform_query_dict_into_regular_dict(request.GET)
            payload = extract_request_payload(request, allow_forms)
            if request.method in HTTP_METHODS_SUPPORTING_PAYLOAD:
                deserializer = deserializers_http_methods_map[request.method](
                    data=payload
                )
                if not deserializer.is_valid():
                    raise BadRequest
                deserialized_data = deserializer.data
            else:
                deserialized_data = None

            return view_function(
                request,
                url_params=kwargs,
                query_params=query_params,
                deserialized_data=deserialized_data,
            )
        except BaseAPIException as e:
            return JsonResponse({"error_msg": e.RESPONSE_MESSAGE}, status=e.STATUS_CODE)
        except Exception:
            return JsonResponse(
                {"error_msg": InternalServerError.RESPONSE_MESSAGE},
                status=InternalServerError.STATUS_CODE,
            )

    return function_wrapper


def build_class_wrapper(
    permission_class,  # type: BasePermission
    allowed_methods,  # type: Iterable[str]
    deserializers_http_methods_map,  # type: Dict[str, ClassVar[Deserializer]]
    allow_forms,  # type: bool
    view_class,  # type: ClassVar
):  # type:(...) -> ClassVar
    class ViewWrapper(View):
        __doc__ = view_class.__doc__
        __module__ = view_class.__module__
        __slots__ = "_wrapped_view"

        def __init__(self, *args, **kwargs):
            self._wrapped_view = view_class(*args, **kwargs)

        def dispatch(self, request, *args, **kwargs):
            # type:(HttpRequest, List[Any]) -> JsonResponse
            # No need for additional check on request.method, since it's been
            # already checked
            handler = getattr(self, request.method.lower())
            return handler(request, *args, **kwargs)

        def __getattribute__(self, name):
            try:
                return super(ViewWrapper, self).__getattribute__(name)
            except AttributeError:
                attribute = self._wrapped_view.__getattribute__(name)
                if (
                    not inspect.ismethod(attribute)
                    or name.upper() not in ALL_HTTP_METHODS
                ):
                    return attribute
                return build_function_wrapper(
                    permission_class,
                    allowed_methods,
                    deserializers_http_methods_map,
                    allow_forms,
                    attribute,
                )

    ViewWrapper.__name__ = view_class.__name__
    return ViewWrapper
