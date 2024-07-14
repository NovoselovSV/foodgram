import csv

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import reverse

from . import serializers
from .filters import OrderingSearchFilter, RecipeFilter
from .m2m_model_actions import create_or_delete_connection_shortcut
from .permissions import AuthorOnly, ReadOnly
from core import models

User = get_user_model()


class UserViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """ViewSet for user flows."""

    @action(detail=False, methods=('get',),
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        self.kwargs['pk'] = request.user.id
        return self.retrieve(request)

    @action(detail=False,
            methods=('put', 'delete'),
            permission_classes=(permissions.IsAuthenticated,),
            url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializers.AvatarSerializer(
            user, data=request.data, context={
                'request': request})
        serializer.is_valid(raise_exception=True)
        if user.avatar and user.avatar.name != 'users/default.png':
            user.avatar.delete(save=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(('post',), detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def set_password(self, request):
        serializer = serializers.UserPasswordWriteOnly(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        if not user.check_password(serializer.data['current_password']):
            return Response(
                data={'error': 'Wrong password'},
                status=status.HTTP_400_BAD_REQUEST)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(('get',), detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        return self.get_all_subscriptions_response(request)

    @action(('post', 'delete'), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, pk):
        subscription = get_object_or_404(User, pk=pk)
        connection_info = {'subscription': subscription,
                           'subscriber': request.user}
        return create_or_delete_connection_shortcut(
            models.Subscription,
            connection_info,
            request,
            self.get_subscription_queryset(),
            serializers.UserRecipeReadSerializer,
            response_pk=pk)

    def get_subscription_queryset(self):
        return self.get_queryset().annotate(
            recipes_count=Count('recipes')).prefetch_related('recipes').filter(
            is_subscribed=True)

    def get_all_subscriptions_response(self, request):
        return self.get_paginated_response(
            serializers.UserRecipeReadSerializer(
                self.paginate_queryset(
                    self.get_subscription_queryset()),
                context={'request': request},
                many=True).data)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.UserReadSerializer
        return serializers.UserWriteSerializer

    def get_queryset(self):
        return User.objects.add_is_subscribed_annotate(
            self.request.user.id)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading ingredients."""

    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (OrderingSearchFilter,)
    search_fields = ('^name', 'name')
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading tags."""

    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for recipes."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          AuthorOnly | ReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer

    def get_queryset(self):
        return (models.Recipe.objects.prefetch_related(
            Prefetch(
                'author',
                queryset=User.objects.add_is_subscribed_annotate(
                    self.request.user.id)),
            'tags',
            Prefetch(
                'ingredient_many_table',
                queryset=models.RecipeIngredient.
                objects.select_related('ingredient'))).
                add_all_annotations(self.request.user.id))

    @action(methods=('get',), detail=True, url_path='get-link')
    def get_link(self, request, pk):
        return Response(
            data={'short-link': reverse('short-link',
                                        kwargs={'pk': pk},
                                        request=request)})

    @action(methods=('post', 'delete'), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        connection_info = {
            'recipe': recipe,
            'user': request.user}
        return create_or_delete_connection_shortcut(
            models.UserRecipeFavorite,
            connection_info,
            request,
            recipe,
            serializers.RecipeShortSerializer)

    @action(methods=('post', 'delete'), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        connection_info = {
            'recipe': recipe,
            'user': request.user}
        return create_or_delete_connection_shortcut(
            models.UserRecipeShoppingList,
            connection_info,
            request,
            recipe,
            serializers.RecipeShortSerializer)

    @action(('get',), detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = models.RecipeIngredient.objects.filter(
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
