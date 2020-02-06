import re

from companies.models import Company

company_matching_regex = re.compile(r"/c/([\w-]+)")


class AttachCompanyMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def attach_company_if_exists(self, request):
        company = None

        ### TESTING
        request.company = Company.objects.first()
        return
        ###

        if "HTTP_REFERER" in request.META:
            company_match = company_matching_regex.search(request.META["HTTP_REFERER"])

            if company_match:
                company_short_name = company_match.group(1)
                company = Company.objects.filter(short_name=company_short_name).first()
                request.company = company

        request.company = company

    def __call__(self, request):
        self.attach_company_if_exists(request)
        response = self.get_response(request)
        return response
