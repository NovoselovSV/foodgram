from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.models import Subscription

from .serializers import UserReadSerializer, UserWriteSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user flows."""
    http_method_names = ('get', 'post')
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('username',)
    # lookup_field = 'username'

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        self.kwargs['username'] = request.user.username
        return self.retrieve(request)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserWriteSerializer

    def get_queryset(self):
        return User.objects.annotate(
            is_subscribed=Exists(
                Subscription.objects.filter(
                    subscriber=self.request.user.id,
                    subscription=OuterRef('pk'))))
