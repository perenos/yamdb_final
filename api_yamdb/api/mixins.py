from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import AllowAny
from api.permissions import IsAdmin


class ListCreateDestroyViewSet(mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action == 'list':
            return (AllowAny(),)
        return (IsAdmin(),)
