from django.conf import settings
from django.contrib import admin
from django.urls import include, path, register_converter

from core.converters import Base64Converter
from core.views import redirect_short_link

register_converter(Base64Converter, 'b64url')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<b64url:pk>/', redirect_short_link, name='short-link')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
