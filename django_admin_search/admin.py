# region				-----External Imports-----
from django.contrib.admin.views.main import ChangeList
from django.utils.translation import gettext_lazy as _
import django
import typing
# endregion

# region				-----Internal Imports-----
from . import utils
# endregion

# region		      -----Supporting Variables-----
MULTIPLE_CHOICE_FIELDS = (
    django.forms.ModelMultipleChoiceField,
    django.forms.MultipleChoiceField
)
# endregion


class AdvancedSearchChangeList(ChangeList):
    def __init__(self,
            request,
            model,
            list_display,
            list_display_links,
            list_filter,
            date_hierarchy,
            search_fields,
            list_select_related,
            list_per_page,
            list_max_show_all,
            list_editable,
            model_admin,
            sortable_by,
            search_help_text: str = "",
        ):
        # ? Get our advanced_search_fields and store them inside
        # ? ChangeList class so we can use them in the future
        # ? for adding into generated links for pagination,
        # ? sorting and .etc
        self.custom_filters = model_admin.advanced_search_fields
        
        super().__init__(
            list_select_related=list_select_related,
            list_display_links=list_display_links, 
            list_max_show_all=list_max_show_all, 
            search_help_text=search_help_text,
            date_hierarchy=date_hierarchy, 
            search_fields=search_fields, 
            list_per_page=list_per_page, 
            list_editable=list_editable, 
            list_display=list_display, 
            list_filter=list_filter, 
            model_admin=model_admin, 
            sortable_by=sortable_by, 
            request=request, 
            model=model
        )

    def get_query_string(self, 
            new_params: typing.Dict = None, 
            remove: typing.Dict = None
        ) -> typing.AnyStr:
        # ? Let Django make his work so we can make our
        query_string = super().get_query_string(
            new_params=new_params, 
            remove=remove
        )

        # ? Append additional parameters to the result
        # ? query so we can handle sorting, pagination
        # ? and .etc without breaking Django 
        # ? core functionality
        for key, value in self.custom_filters.items():
            if isinstance(value, list):
                for subvalue in value:
                    query_string += f"&{key}={subvalue}"
            else:
                query_string += f"&{key}={value}"
        
        return query_string


class AdvancedSearchAdmin(
        django.contrib.admin.ModelAdmin
    ):
    change_list_template = 'admin/custom_change_list.html'
    advanced_search_fields = {}
    search_form_data = None


    @staticmethod
    def get_field_value_default(
            request: django.http.HttpRequest,
            form_field: django.forms.Field,
            field_value: typing.Any, 
            has_field_value: bool, 
            field: typing.AnyStr, 
        ) -> django.db.models.Q:
        if has_field_value:
            # ? Get attributes from the widgets so we can clearly understand
            # ? which filters and how we have to apply to the queryset
            field_filter = form_field.widget.attrs.get("filter_field", field)\
                         + form_field.widget.attrs.get("filter_method", "")
            
            field_name = form_field.widget.attrs.get("filter_field", field)
            
            try:
                # ? Generate model.Q object relying on the data provided 
                # ? from the request for the future filtering purposes
                field_value = utils.format_data(form_field, field_value)
                return django.db.models.Q(**{field_filter: field_value})
            
            except django.core.exceptions.ValidationError:
                django.contrib.messages.add_message(
                    message=_(f"Field: `{field_name}` isn't valid"),
                    level=django.contrib.messages.ERROR, 
                    request=request
                )
            
            except Exception:
                django.contrib.messages.add_message(
                    message=_(f"Error in `{field_name}` field"),
                    level=django.contrib.messages.ERROR,
                    request=request, 
                )

        return django.db.models.Q()


    def changelist_view(self, 
            request: django.http.HttpRequest, 
            extra_context: typing.Dict = None
        ) -> ChangeList:
        if hasattr(self, "search_form"):
            self.advanced_search_fields = {}

            # ? Ensure that all the values from the QueryDict will be 
            # ? parsed correctly is case we have keys that have 
            # ? multiple values inside
            self.search_form_data = self.search_form(
                django.utils.datastructures.MultiValueDict(request.GET)
            )
            
            # ? Clear the incoming request from query parameters that 
            # ? may break Django core logic because of origin
            self.extract_advanced_search_terms(request=request.GET)

            extra_context = {
                "form": self.search_form_data,
                "fieldsets": []
            }

        return super().changelist_view(
            extra_context=extra_context,
            request=request, 
        )


    def get_request_field_value(self, 
            form_field: django.forms.Field,
            field: typing.AnyStr, 
        ):
        # ? Map correctly fields that may contain multiple 
        # ? values inside and single value
        if field in self.advanced_search_fields:
            if not isinstance(form_field, MULTIPLE_CHOICE_FIELDS):
                return True, self.advanced_search_fields[field][0]
            else:
                return True, self.advanced_search_fields[field]

        return False, None


    def extract_advanced_search_terms(self, 
            request: django.http.HttpRequest
        ) -> django.http.HttpRequest:
        request._mutable = True

        # ? Remove keys that may break Django core 
        # ? logic from the request object
        if self.search_form_data is not None:
            for key in self.search_form_data.fields.keys():
                temp = request.pop(key, None)

                if temp:
                    self.advanced_search_fields[key] = temp

        request._mutable = False


    def get_field_value(self, 
            request: django.http.HttpRequest,
            form_field: django.forms.Field,
            field_value: typing.Any, 
            has_field_value: bool, 
            field: typing.AnyStr, 
        ) -> django.db.models.Q:
        # ? Get custom defined filtering rule if
        #? it exists for the appropriate field
        function = getattr(self, "search_" + field, None)

        if function:
            kwargs = {
                "param_values": self.advanced_search_fields,
                "field_value": field_value,
                "form_field": form_field,
                "request": request,
                "field": field,
            }

            return function(**kwargs)

        return self.get_field_value_default(
            has_field_value=has_field_value, 
            field_value=field_value, 
            form_field=form_field, 
            request=request,
            field=field
        )


    def get_queryset(self, 
            request: django.http.HttpRequest
        ) -> django.db.models.QuerySet:
        queryset = super().get_queryset(request=request)

        try:
            # ? Filter our queryset object with provided 
            # ? filter options from the form
            filters = self.advanced_search_query(
                request=request
            )
            
            return queryset.filter(filters)
        
        except Exception:
            django.contrib.messages.add_message(
                level=django.contrib.messages.ERROR, 
                message="Filter was not applied",
                request=request
            )

            return queryset.none()


    def advanced_search_query(self,
            request: django.http.HttpRequest
        ) -> django.db.models.Q:
        query = django.db.models.Q()

        if self.search_form_data is None:
            return query

        fields = self.search_form_data.fields.items()

        for field, form_field in fields:
            has_field_value, field_value =\
                self.get_request_field_value(
                    form_field=form_field, 
                    field=field
                )

            query &= self.get_field_value(
                has_field_value=has_field_value, 
                field_value=field_value, 
                form_field=form_field, 
                request=request,
                field=field, 
            )

        return query


    def get_changelist(self, 
            request: django.http.HttpRequest, 
            **kwargs: typing.Dict
        ) -> ChangeList:
        return AdvancedSearchChangeList
