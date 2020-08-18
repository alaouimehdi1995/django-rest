# -*- coding: utf-8 -*-

import ujson
from django.http import HttpResponse


class JsonResponse(HttpResponse):
    def __init__(self, content, charset=None, status=200):
        content_type = "application/json"
        content = ujson.dumps(content)
        super(JsonResponse, self).__init__(
            content=content, content_type=content_type, charset=charset, status=status
        )
