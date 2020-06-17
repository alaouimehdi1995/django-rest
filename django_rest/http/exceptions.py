# -*- coding: utf-8 -*-

from django_rest.http import status


class BaseAPIException(Exception):
    """
    Base API exception from which all specific exceptions will inherit.
    The exception defines a `STATUS_CODE` attribute and a `RESPONSE_MESSAGE`
    Those attributes are used by `api_view()` decorator, to return a readable
    `JsonResponse()` with a valid message and status code, without having to catch
    exceptions inside the view.
    """

    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    RESPONSE_MESSAGE = "An unknown server error occured."


class BadRequest(BaseAPIException):
    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    RESPONSE_MESSAGE = "Bad request."


class NotAuthenticated(BaseAPIException):
    STATUS_CODE = status.HTTP_401_UNAUTHORIZED
    RESPONSE_MESSAGE = "Unauthorized operation. Maybe forgot the authentication step ?"


class PermissionDenied(BaseAPIException):
    STATUS_CODE = status.HTTP_403_FORBIDDEN
    RESPONSE_MESSAGE = "Forbidden operation. Make sure you have the right permissions."


class NotFound(BaseAPIException):
    STATUS_CODE = status.HTTP_404_NOT_FOUND
    RESPONSE_MESSAGE = "The requested resource is not found."


class MethodNotAllowed(BaseAPIException):
    STATUS_CODE = status.HTTP_405_METHOD_NOT_ALLOWED
    RESPONSE_MESSAGE = "HTTP Method not allowed."


class UnsupportedMediaType(BaseAPIException):
    STATUS_CODE = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    RESPONSE_MESSAGE = "Unsupported Media Type. Check your request's Content-Type."


class InternalServerError(BaseAPIException):
    pass


class ServiceUnavailable(BaseAPIException):
    STATUS_CODE = status.HTTP_503_SERVICE_UNAVAILABLE
    RESPONSE_MESSAGE = "The requested service is unavailable."
