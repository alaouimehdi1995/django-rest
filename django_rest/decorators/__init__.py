# -*- coding: utf-8 -*-

import inspect

from django.views import View

from django_rest.decorators.utils import (
    build_class_wrapper,
    build_deserializer_map,
    build_function_wrapper,
)
from django_rest.deserializers import AllPassDeserializer, Deserializer
from django_rest.http.methods import ALL_METHODS
from django_rest.permissions import AllowAny, BasePermission

FORMS_CONTENT_TYPES = (
    "application/x-www-form-urlencoded",
    "multipart/form-data",
)


def api_view(
    permission_class=AllowAny,  # type: Union[AbstractPermission, Any]
    allowed_methods=ALL_METHODS,  # type: Tuple[str]
    deserializer_class=AllPassDeserializer,  # type: Union[ClassVar[Deserializer], Dict[str, ClassVar[Deserializer]]]
    allow_forms=False,  # type: bool
):  # type:(...) -> Callable

    if not (
        inspect.isclass(permission_class)
        and issubclass(permission_class, BasePermission)
    ):
        # In case the decorator's called without parenthesis (`@api_view`),
        # the `permission_class` variable holds the real view.
        return api_view()(permission_class)

    deserializers_http_methods_map = build_deserializer_map(deserializer_class)

    def view_decorator(view):
        # type:(Union[Callable, ClassVar]) -> Union[Callable, ClassVar]
        if inspect.isfunction(view):
            return build_function_wrapper(
                permission_class,
                allowed_methods,
                deserializers_http_methods_map,
                allow_forms,
                view,
            )
        elif inspect.isclass(view) and issubclass(view, View):
            return build_class_wrapper(
                permission_class,
                allowed_methods,
                deserializers_http_methods_map,
                allow_forms,
                view,
            )
        given_str = (
            "{} class".format(view.__name__)
            if inspect.isclass(view)
            else "{} object".format(view.__class__.__name__)
        )
        raise TypeError(
            "The `@api_view` decorator is applied to either a function or a "
            "class inheriting from django.views.View. Given: {}".format(given_str)
        )

    return view_decorator
