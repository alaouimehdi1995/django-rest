# -*- coding: utf-8 -*-

"""
For more details: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
"""


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

SAFE_METHODS = (GET, HEAD, OPTIONS)

SUPPORTING_PAYLOAD_METHODS = (
    POST,
    PUT,
    PATCH,
)

ALL_METHODS = (
    HEAD,
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
    OPTIONS,
    TRACE,
    CONNECT,
)
