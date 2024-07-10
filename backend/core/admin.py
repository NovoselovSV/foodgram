from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Ingredient, Subscription, Tag, User

admin.site.register(Subscription)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(User, UserAdmin)
