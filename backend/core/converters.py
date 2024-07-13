from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class Base64Converter:
    """URL path convertor urlsafe_base64 to integer."""

    regex = '[A-Za-z0-9_-]+=*'

    def to_python(self, value):
        return int.from_bytes(urlsafe_base64_decode(value))

    def to_url(self, value):
        return urlsafe_base64_encode(int(value).to_bytes())
