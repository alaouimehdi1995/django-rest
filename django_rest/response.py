def to_bytes(val, encoding):
    return val if isinstance(val, bytes) else val.encode(encoding)


import json
from http.client import responses


class JsonResponse:
    streaming = False

    def __init__(
        self,
        content,
        status_code=200,
        content_type="application/json",
        additional_headers={},
    ):
        self.content = json.dumps(content).encode()
        self.status_code = int(status_code)
        self.reason_phrase = responses.get(status_code, "Unknown Status Code")
        self._content_type = content_type
        self._headers = {
            "Content-Type".lower(): ("Content-Type", content_type),
        }
        self._headers.update({k.lower(): (k, v) for k, v in additional_headers.items()})
        self._closable_objects = []
        self.cookies = {}

    def __repr__(self):
        return "<%(cls)s status_code=%(status_code)d%(content_type)s>" % {
            "cls": self.__class__.__name__,
            "status_code": self.status_code,
            "content_type": self._content_type,
        }

    def get(self, header, alternate=None):
        return self._headers.get(header.lower(), (None, alternate))[1]

    def __getitem__(self, header):
        return self._headers[header.lower()][1]

    def items(self):
        return self._headers.values()

    def has_header(self, header):
        """Case-insensitive check for a header."""
        return header.lower() in self._headers

    __contains__ = has_header

    def serialize_headers(self):
        headers = [
            (to_bytes(key, "ascii") + b": " + to_bytes(value, "latin-1"))
            for key, value in self._headers.values()
        ]
        return b"\r\n".join(headers)

    # __bytes__ = serialize_headers
    def __setitem__(self, header, value):
        # header = self._convert_to_charset(header, 'ascii')
        # value = self._convert_to_charset(value, 'latin-1', mime_encode=True)
        self._headers[header.lower()] = (header, value)

    def __iter__(self):
        return iter([self.content])

    def has_header(self, header):
        """Case-insensitive check for a header."""
        return header.lower() in self._headers

    def serialize(self):
        """Full HTTP message, including headers, as a bytestring."""
        return self.serialize_headers() + b"\r\n\r\n" + self.content

    def set_cookie(self, *args, **kwargs):
        pass
