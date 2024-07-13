from django.shortcuts import redirect


def redirect_short_link(request, pk):
    """Simple redirect to main url recipe from short link."""
    return redirect(request.build_absolute_uri(f'/recipes/{pk}'))
