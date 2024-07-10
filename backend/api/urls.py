from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import IngredientViewSet, TagViewSet, UserViewSet

app_name = 'api'

router = SimpleRouter()
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
