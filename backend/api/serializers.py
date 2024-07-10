import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from core.models import Ingredient

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """User serializer for reading."""
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
