# -*- coding: utf-8 -*-


from flash_rest.http.exceptions import BaseAPIException


class SerializationError(BaseAPIException):
    """ Raised when a serialization error occurs (required field that is not found, etc.) """
