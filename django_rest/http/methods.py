# -*- coding: utf-8 -*-

from enum import Enum

"""
For more details: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
"""


class HTTPMethods(str, Enum):
    # Read-only methods
    HEAD = "HEAD"
    GET = "GET"
    # Writing methods
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    # Special methods
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


SAFE_METHODS = (HTTPMethods.GET, HTTPMethods.HEAD, HTTPMethods.OPTIONS)
WRITING_METHODS = (
    HTTPMethods.POST,
    HTTPMethods.PUT,
    HTTPMethods.PATCH,
    HTTPMethods.DELETE,
)
ALL_METHODS = tuple(attribute.value for attribute in HTTPMethods)
