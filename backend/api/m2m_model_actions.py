from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.db.models.deletion import IntegrityError
from rest_framework import status
from rest_framework.response import Response


def create_connection(model, **kwargs):
    """Create link in m2m model. If errors occure return response object."""
    try:
        model.objects.create(**kwargs)
    except IntegrityError as error:
        return Response(
            data={'errors': settings.
                  ERROR_M2M_CONNECTION_MSGS[error.args[0]]},
            status=status.HTTP_400_BAD_REQUEST)


def delete_connection(model, **kwargs):
    """Delete link in m2m model. If errors occure return response object."""
    try:
        model.objects.get(**kwargs).delete()
    except ObjectDoesNotExist:
        return Response(
            data={'errors': settings.NOT_CONNECTED_MSG},
            status=status.HTTP_400_BAD_REQUEST)


def create_or_delete_connection_shortcut(
        model,
        connection_m2m_info,
        request,
        response_object,
        response_serializer_cls,
        response_pk=None):
    if request.method == 'POST':
        error_response = create_connection(model=model, **connection_m2m_info)
        if not error_response and response_pk:
            response_object = response_object.get(pk=response_pk)
        return error_response or Response(
            data=response_serializer_cls(
                response_object,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED)

    error_response = delete_connection(model=model, **connection_m2m_info)
    return error_response or Response(status=status.HTTP_204_NO_CONTENT)
