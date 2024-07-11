from django.shortcuts import redirect
from rest_framework.viewsets import reverse


def redirect_short_link(request, pk):
    return redirect(
        reverse(
            'api:recipes-detail',
            kwargs={
                'pk': pk},
            request=request))
