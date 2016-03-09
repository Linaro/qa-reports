from rest_framework import pagination
from rest_framework import response


class Pagination(pagination.PageNumberPagination):

    def paginate_queryset(self, queryset, request, view=None):
        if 'no_pagination' in request.query_params:
            return None
        return super(Pagination, self).paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if self.page.has_next():
            next_page = self.page.next_page_number()
        else:
            next_page = None

        if self.page.has_previous():
            previous_page = self.page.previous_page_number()
        else:
            previous_page = None

        self.page.has_previous()

        return response.Response({
            'page': {
                'next': next_page,
                'previous': previous_page
            },
            'count': self.page.paginator.count,
            'results': data
        })
