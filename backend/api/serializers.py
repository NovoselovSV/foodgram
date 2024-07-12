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

    is_subscribed = serializers.BooleanField(default=False)
    # is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    # def get_is_subscribed(self, user):
    #     # попытка через annotate во viewset queryset провалена, так как этот
    #     # сериалайзер требуется в другом viewset, попытка через несколько
    #     # annotate провалена так как annotate во viewset recipe не
    #     # подхватывается во вложенном сериалайзере, попытка взять хешироанное
    #     # значение запроса annotate провалена так как с annotate queryset не
    #     # хэшируется, попытка доп. фильтрации на месте провалена так как так
    #     # как создаются доп. запросы, попытка переопределить дефолтный менеджер
    #     # как и другие махинации с моделью провалена так как для annotate нужна
    #     # информация о запросе
    #     # оставшиеся варианты или создавать доп запросы на поиск вхождений или
    #     # самому искать эти вхождения (Последнее реализовано)
    #     return bool(
    #         list(
    #             filter(
    #                 lambda connection: (connection.subscriber_id == self.
    #                                     context['request'].user.id),
    #                 user.subscriptions_many_table.all()
    #             )))


class UserWriteSerializer(UserCreateSerializer):
    """User serializer for writing."""

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        read_only_fields = ('id',)


class Base64ImageField(serializers.ImageField):
    """Base64 to image field convertor."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            data = ContentFile(
                base64.b64decode(imgstr),
                name='image.' + format.split('/')[-1])

        return super().to_internal_value(data)


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
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

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

    def validate(self, data):
        if 'ingredients' in data:
            ingredient_types = set()
            for record in data['ingredients']:
                if record['ingredient'] in ingredient_types:
                    raise serializers.ValidationError(
                        'Один ингредиент добавлен несколько раз')
                ingredient_types.add(record['ingredient'])
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for record in ingredients:
            RecipeIngredient.objects.create(recipe=recipe, **record)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        if 'tags' in validated_data:
            instance.tags.clear()
            for tag in validated_data['tags']:
                instance.tags.add(tag)
        if 'ingredients' in validated_data:
            instance.ingredients.clear()
            for record in validated_data['ingredients']:
                RecipeIngredient.objects.create(recipe=instance, **record)
        instance.save()
        return instance

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Serializer for short recipe info."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserRecipeReadSerializer(UserReadSerializer):
    """Serializer for read user and his recipes info."""

    recipes = RecipeShortSerializer(many=True)
    recipes_count = serializers.IntegerField()

    class Meta(UserReadSerializer.Meta):
        fields = UserReadSerializer.Meta.fields + ('recipes', 'recipes_count')
