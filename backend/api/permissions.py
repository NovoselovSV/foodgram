from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnly(BasePermission):
    """Permission for read only actions."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS


class AuthorOnly(BasePermission):
    """Permission for author only acions."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
