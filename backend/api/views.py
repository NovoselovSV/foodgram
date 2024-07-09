from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Subscription
from .serializers import AvatarSerializer, UserReadSerializer, UserWriteSerializer

User = get_user_model()


class UserViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """ViewSet for user flows."""
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('username',)
    # lookup_field = 'username'

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        self.kwargs['pk'] = request.user.id
        return self.retrieve(request)

    @action(detail=False, methods=('put', 'delete'),
            permission_classes=(IsAuthenticated,), url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            user, data=request.data, context={
                'request': request})
        serializer.is_valid(raise_exception=True)
        if user.avatar:
            user.avatar.delete(save=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(('post',), detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return UserReadSerializer
        return UserWriteSerializer

    def get_queryset(self):
        return User.objects.annotate(
            is_subscribed=Exists(
                Subscription.objects.filter(
                    subscriber=self.request.user.id,
                    subscription=OuterRef('pk'))))
