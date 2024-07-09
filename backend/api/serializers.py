import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """User serializer for reading."""
    is_subscribed = serializers.BooleanField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')


class UserWriteSerializer(serializers.ModelSerializer):
    """User serializer for writing."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        read_only_fields = ('id',)


class Base64ImageField(serializers.ImageField):
    """Base64 to image field convertor."""
    def __init__(self, *args, image_name='', **kwargs):
        self.image_name = image_name
        return super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            data = ContentFile(
                base64.b64decode(imgstr),
                name=self.context['request'].user.username
                + self.image_name
                + '.'
                + format.split('/')[-1])

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for users avatar."""
    image = Base64ImageField(image_name='avatar')

    class Meta:
        model = User
        fields = ('avatar',)
