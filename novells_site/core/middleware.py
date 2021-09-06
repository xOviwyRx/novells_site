from django import http
from django.contrib.sites.models import Site


class MultiSiteMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        print('Hello Marat')
        response = self._get_response(request)
        print(request.get_host())
        """"
        try:
            domain = request.get_host().split(":")[0]
            request.site = Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            return http.HttpResponseNotFound()
        """
        return response
"""
    def process_request(self, request):
        try:
            domain = request.get_host().split(":")[0]
            request.site = Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            return http.HttpResponseNotFound()"""