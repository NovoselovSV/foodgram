from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.db.models.deletion import IntegrityError
from rest_framework import status
from rest_framework.response import Response

from .exceptions import ErrorException


def create_connection(model, **kwargs):
    """Create link in m2m model."""
    try:
        model.objects.create(**kwargs)
    except IntegrityError as error:
        raise ErrorException(settings.
                             ERROR_M2M_CONNECTION_MSGS[error.args[0]])


def delete_connection_n_response(model, **kwargs):
    """Delete link in m2m model. If complete return response object."""
    try:
        model.objects.get(**kwargs).delete()
    except ObjectDoesNotExist:
        raise ErrorException(settings.NOT_CONNECTED_MSG)
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)
