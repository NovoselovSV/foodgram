from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, ObjectDoesNotExist, OuterRef, Prefetch, Value
from django.db.models.deletion import IntegrityError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import reverse

from core.models import Ingredient, Recipe, RecipeIngredient, Subscription, Tag
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserReadSerializer,
    UserRecipeReadSerializer,
    UserWriteSerializer)

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
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(('get',), detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        return self.get_subscription_response(request)

    @action(('post', 'delete'), detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        # Вариант с сериализаторами не подходит так как структура ответа должна
        # быть "error": 'string'
        subscription = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            try:
                Subscription.objects.create(
                    subscription=subscription,
                    subscriber=request.user)
            except IntegrityError as error:
                return Response(
                    data={'errors':
                          settings.RESPONSE_FOLLOW_MSGS[error.args[0]]},
                    status=status.HTTP_400_BAD_REQUEST)
            return self.get_subscription_response(request, pk)

        try:
            Subscription.objects.get(
                subscription=subscription,
                subscriber=request.user).delete()
        except ObjectDoesNotExist:
            return Response(
                data={
                    'errors': settings.NOT_SUBSCRIBED_MSG},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_subscription_response(self, request, pk=None):
        queryset = self.get_queryset().annotate(
            recipes_count=Count('recipes')).prefetch_related('recipes').filter(
            is_subscribed=True)
        if pk:
            return self.get_current_subscription(queryset, request, pk)
        return self.get_all_subscriptions(queryset, request)

    def get_current_subscription(self, queryset, request, pk):
        return Response(
            data=UserRecipeReadSerializer(
                queryset.get(pk=pk), context={'request': request}).data,
            status=status.HTTP_201_CREATED)

    def get_all_subscriptions(self, queryset, request):
        return self.get_paginated_response(
            UserRecipeReadSerializer(
                self.paginate_queryset(queryset), context={
                    'request': request}, many=True).data)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return UserReadSerializer
        return UserWriteSerializer

    def get_queryset(self):
        return User.objects.add_is_subscribed_annotate(
            self.request.user.id, 'pk')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for recipes."""

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    # доделать is_favorited и is_in_shopping_cart
    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            Prefetch(
                'author',
                queryset=User.objects.add_is_subscribed_annotate(
                    self.request.user.id,
                    'pk')),
            'tags',
            Prefetch(
                'ingredient_many_table',
                queryset=RecipeIngredient.
                objects.select_related('ingredient')))

    @action(methods=('get',), detail=True, url_path='get-link')
    def get_link(self, request, pk):
        return Response(
            data={'short-link': reverse('short-link',
                                        kwargs={'pk': pk},
                                        request=request)})
