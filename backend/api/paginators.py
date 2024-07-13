from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class PagePaginationWithLimit(PageNumberPagination):
    """Pagination class for add page_size_query_param."""

    page_size = settings.DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = 100
