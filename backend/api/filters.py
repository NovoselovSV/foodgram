import operator
from functools import reduce

from django.db import models
from django.db.models import Value
from django.db.models.aggregates import Case, When
from rest_framework.compat import distinct
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters

from core.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Filter to Recipe viewset."""

    is_favorited = filters.BooleanFilter(label='is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(label='is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ('author',)


class OrderingSearchFilter(SearchFilter):
    """Search filter for ordering by seach fields."""

    def filter_queryset(self, request, queryset, view):
        """Adding annotation for ordering by it."""
        queryset = super().filter_queryset(request, queryset, view)
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field))
            for search_field in search_fields
        ]

        orderings = []
        for search_term in search_terms:
            queries = [
                models.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            orderings.append(queries)
        queryset = (queryset.annotate(
            order_mark=Case(
                *(When(q_object, then=Value(order_mark))
                    for order_mark,
                    q_object in enumerate(*orderings)))).
            order_by('order_mark'))
        return queryset
