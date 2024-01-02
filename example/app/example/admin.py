from django.contrib.admin import register
from django.db.models import Q

from django_admin_search.admin import AdvancedSearchAdmin

from .form import AreaForm, AreaSearchForm
from .models import Area
import django

class AnnotatedValues(django.contrib.admin.ModelAdmin):
    def get_queryset(self, 
            request: django.http.HttpRequest
        ) -> django.db.models.QuerySet:
        # ? Add your annotations here
        return super().get_queryset(request=request)


@register(Area)
class AreaAdmin(AdvancedSearchAdmin, AnnotatedValues):
    # ? To make annotations work correctly with AdvancedSearch we have to make 
    # ? a small trick with MRO of python inheritance
    form = AreaForm
    search_form = AreaSearchForm


    def search_description(self, 
            field, 
            field_value, 
            form_field, 
            request, 
            param_values
        ):
        query = Q()
        # ? Your Q logic here
        return query
