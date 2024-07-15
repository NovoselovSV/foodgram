import csv

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Prefetch, Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import reverse

from . import serializers
from .exceptions import InnerException
from .filters import OrderingSearchFilter, RecipeFilter
from .m2m_model_actions import create_connection, delete_connection_n_response
from .permissions import AuthorOnly, ReadOnly
from core import models

User = get_user_model()


class UserViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """ViewSet for user flows."""

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        self.kwargs['pk'] = request.user.id
        return self.retrieve(request)

    @action(detail=False,
            methods=('put',),
            permission_classes=(permissions.IsAuthenticated,),
            url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        serializer = serializers.AvatarSerializer(
            user, data=request.data, context={
                'request': request})
        serializer.is_valid(raise_exception=True)
        if user.avatar:
            user.avatar.delete(save=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(('post',), detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def set_password(self, request):
        serializer = serializers.UserPasswordWriteOnly(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        user.set_password(serializer.data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        return self.get_all_subscriptions_response(request)

    @action(('post',), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, pk):
        return (create_connection(
            model=models.Subscription,
            subscription=get_object_or_404(User, pk=pk),
            subscriber=request.user)
            or Response(
            data=serializers.UserRecipeReadSerializer(
                self.get_subscription_queryset().get(
                    pk=pk),
                context={'request': request}).data,
            status=status.HTTP_201_CREATED))

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk):
        return delete_connection_n_response(
            model=models.Subscription,
            subscription=get_object_or_404(User, pk=pk),
            subscriber=request.user)

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

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve', 'me'}:
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
        if self.action in {'list', 'retrieve'}:
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

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk):
        return Response(
            data={'short-link': reverse('short-link',
                                        kwargs={'pk': pk},
                                        request=request)})

    @action(methods=('post',), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        return (create_connection(
            model=models.UserRecipeFavorite,
            recipe=recipe,
            user=request.user)
            or Response(
            data=serializers.RecipeShortSerializer(
                recipe,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED))

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return delete_connection_n_response(
            models.UserRecipeFavorite,
            recipe=get_object_or_404(
                models.Recipe,
                pk=pk),
            user=request.user)

    @action(methods=('post',), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        return (create_connection(
            model=models.UserRecipeShoppingList,
            recipe=recipe,
            user=request.user)
            or Response(
            data=serializers.RecipeShortSerializer(
                recipe,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED))

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        return delete_connection_n_response(
            models.UserRecipeShoppingList,
            recipe=get_object_or_404(
                models.Recipe,
                pk=pk),
            user=request.user)

    @action(detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = models.RecipeIngredient.objects.filter(
            recipe__in_shopping_list_by=request.user).values(
            ingredients_name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')).annotate(
            total_amount=Sum('amount'))
        with open('temp.csv', 'w', newline='') as csvfile:
            fieldnames = (
                'Название ингредиента',
                'Единицы измерения',
                'Количество')
            writer = csv.writer(csvfile)
            writer.writerow(fieldnames)
            writer.writerows(ingredient.values() for ingredient in ingredients)
        return FileResponse(open('temp.csv', 'rb'), as_attachment=True)
