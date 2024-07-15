from rest_framework import status
from rest_framework.exceptions import APIException


class ErrorException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Something in provided data wrong'
    default_code = 'errors'
