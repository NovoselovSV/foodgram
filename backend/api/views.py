import csv

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import (
    Count,
    Exists,
    ObjectDoesNotExist,
    OuterRef,
    Prefetch,
    Sum,
    Value)
from django.db.models.deletion import IntegrityError
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import reverse

from core.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
    UserRecipeFavorite,
    UserRecipeShoppingList)
from .filters import RecipeFilter, OrderingSearchFilter
from .m2m_model_actions import (
    create_connection,
    create_or_delete_connection_shortcut,
    delete_connection)
from .permissions import ReadOnly, AuthorOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
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

    @action(('post',), detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(('get',), detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        return self.get_all_subscriptions_response(request)

    @action(('post', 'delete'), detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        # Вариант с сериализаторами не подходит так как структура ответа должна
        # быть "error": 'string'
        subscription = get_object_or_404(User, pk=pk)
        connection_info = {'subscription': subscription,
                           'subscriber': request.user}
        return create_or_delete_connection_shortcut(
            Subscription,
            connection_info,
            request,
            self.get_subscription_queryset(),
            UserRecipeReadSerializer,
            response_pk=pk)

    def get_subscription_queryset(self):
        return self.get_queryset().annotate(
            recipes_count=Count('recipes')).prefetch_related('recipes').filter(
            is_subscribed=True)

    def get_all_subscriptions_response(self, request):
        return self.get_paginated_response(
            UserRecipeReadSerializer(
                self.paginate_queryset(
                    self.get_subscription_queryset()),
                context={'request': request},
                many=True).data)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return UserReadSerializer
        return UserWriteSerializer

    def get_queryset(self):
        return User.objects.add_is_subscribed_annotate(
            self.request.user.id)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (OrderingSearchFilter,)
    search_fields = ('^name', 'name')
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for recipes."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,
                          AuthorOnly | ReadOnly,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        return (Recipe.objects.prefetch_related(
            Prefetch(
                'author',
                queryset=User.objects.add_is_subscribed_annotate(
                    self.request.user.id)),
            'tags',
            Prefetch(
                'ingredient_many_table',
                queryset=RecipeIngredient.
                objects.select_related('ingredient'))).
                add_all_annotations(self.request.user.id))

    @action(methods=('get',), detail=True, url_path='get-link')
    def get_link(self, request, pk):
        return Response(
            data={'short-link': reverse('short-link',
                                        kwargs={'pk': pk},
                                        request=request)})

    @action(methods=('post', 'delete'), detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        connection_info = {
            'recipe': recipe,
            'user': request.user}
        return create_or_delete_connection_shortcut(
            UserRecipeFavorite,
            connection_info,
            request,
            recipe,
            RecipeShortSerializer)

    @action(methods=('post', 'delete'), detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        connection_info = {
            'recipe': recipe,
            'user': request.user}
        return create_or_delete_connection_shortcut(
            UserRecipeShoppingList,
            connection_info,
            request,
            recipe,
            RecipeShortSerializer)

    @action(('get',), detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_list_by=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(
            total_amount=Sum('amount'))
        with open('temp.csv', 'w', newline='') as csvfile:
            fieldnames = (
                'Название ингредиента',
                'Единицы измерения',
                'Количество')
            writer = csv.writer(csvfile)
            writer.writerow(fieldnames)
            writer.writerows(ingredient.values() for ingredient in ingredients)
        with open('temp.csv', 'r', newline='') as csvfile:
            return HttpResponse(csvfile, content_type='text/csv')

        return Response(data={'errors': 'Site error'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
