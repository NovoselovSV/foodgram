import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from core.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """User serializer for reading."""

    # Реализован вариант который требует принудительной аннотации is_.* полей,
    # а не через SerializerMethodField поскольку последний будет в неявном
    # виде обращаться к БД (self.context['request'].user in
    # recipe.<related_name>.user), что будет приводить к большому числу
    # запросов и не будет вызывать ошибку если забыть сделать prefetch_related
    is_subscribed = serializers.BooleanField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')


class UserWriteSerializer(UserCreateSerializer):
    """User serializer for writing."""

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        read_only_fields = ('id',)


class UserPasswordWriteOnly(serializers.Serializer):
    """Serializer for user password."""

    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate_current_password(self, password):
        if not self.context['request'].user.check_password(password):
            raise serializers.ValidationError('Wrong password')
        return password


class Base64ImageField(serializers.ImageField):
    """Base64 to image field convertor."""

    def to_internal_value(self, b64_image):
        if isinstance(b64_image, str) and b64_image.startswith('data:image'):
            format, imgstr = b64_image.split(';base64,')
            extension = format.split('/')[-1]
            b64_image = ContentFile(
                base64.b64decode(imgstr),
                name=f'image.{extension}')

        return super().to_internal_value(b64_image)


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for users avatar."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientWriteConnectSerializer(serializers.ModelSerializer):
    """Serializer for write connection ingredient to recipe."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, amount):
        if amount < settings.MIN_AMOUNT:
            raise serializers.ValidationError(
                'Количество ингридиента должно '
                f'быть не меньше {settings.MIN_AMOUNT}')
        return amount


class IngredientReadConnectorSerializer(serializers.ModelSerializer):
    """Serializer for read connection ingredient to recipe."""

    class Meta:
        model = RecipeIngredient
        fields = ('amount',)

    def to_representation(self, connection):
        ingredient_data = IngredientSerializer(connection.ingredient).data
        amount_data = super().to_representation(connection)
        return {**ingredient_data, **amount_data}


class RecipeReadSerializer(serializers.ModelSerializer):
    """Serializer for reading recipes."""

    author = UserReadSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientReadConnectorSerializer(
        many=True, source='ingredient_many_table')
    # Реализован вариант который требует принудительной аннотации is_.* полей,
    # а не через SerializerMethodField поскольку последний будет в неявном
    # виде обращаться к БД (self.context['request'].user in
    # recipe.<related_name>.user), что будет приводить к большому числу
    # запросов и не будет вызывать ошибку если забыть сделать prefetch_related
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer for writing recipes."""

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, allow_empty=False)
    ingredients = IngredientWriteConnectSerializer(
        many=True, allow_empty=False)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time')
        patch_required_fields = (
            'tags',
            'ingredients',
            'name',
            'text',
            'cooking_time')

    def validate(self, data):
        empty_value_errors = {}
        for field_name in self.Meta.patch_required_fields:
            if field_name not in data:
                try:
                    self.fail('required')
                except serializers.ValidationError as error:
                    empty_value_errors[field_name] = error.detail
        if empty_value_errors:
            raise serializers.ValidationError(empty_value_errors)
        return data

    def validate_tags(self, tags):
        tag_types = set()
        for tag in tags:
            if tag in tag_types:
                raise serializers.ValidationError(
                    'Один тег добавлен несколько раз')
            tag_types.add(tag)
        return tags

    def validate_ingredients(self, ingredients):
        ingredient_types = set()
        for record in ingredients:
            if 'ingredient' not in record:
                raise serializers.ValidationError(
                    'Запись об ингредиенте без ингредиента')
            ingredient = record['ingredient']
            if ingredient in ingredient_types:
                raise serializers.ValidationError(
                    'Один ингредиент добавлен несколько раз')
            ingredient_types.add(ingredient)
        return ingredients

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.add_m2m_connections(recipe, tags, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        recipe.image = validated_data.pop('image', recipe.image)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        self.add_m2m_connections(recipe, tags, ingredients)
        return super().update(recipe, validated_data)

    def add_m2m_connections(self, recipe, tags, ingredients):
        recipe.tags.set(tags, clear=True)
        recipe.ingredients.clear()
        RecipeIngredient.objects.bulk_create(
            (RecipeIngredient(recipe=recipe, **record)
                for record
                in ingredients))

    def to_representation(self, recipe):
        recipe.author.is_subscribed = False
        recipe.is_favorited = False
        recipe.is_in_shopping_cart = False
        return RecipeReadSerializer(recipe, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Serializer for short recipe info."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserRecipeReadSerializer(UserReadSerializer):
    """Serializer for read user and his recipes info."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta(UserReadSerializer.Meta):
        fields = UserReadSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, user):
        try:
            recipes_limit = int(self.context['request'].query_params.get(
                'recipes_limit'))
        except (ValueError, TypeError):
            recipes_limit = None
        serializer = RecipeShortSerializer(user.recipes, many=True)
        if recipes_limit:
            return serializer.data[:recipes_limit]
        return serializer.data
